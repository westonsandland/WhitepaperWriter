import openai
from pathlib import Path
from langchain.tools import Tool, StructuredTool
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from functools import partial
import os

AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_ENDPOINT = "https://openai-cmh-eastus2.openai.azure.com/"
AZURE_OPENAI_MODEL_NAME = "o1-preview"
AZURE_OPENAI_MODEL = "cmh-eastus2-o1-preview"
AZURE_OPENAI_PREVIEW_API_VERSION = "2024-09-01-preview"
AZURE_OPENAI_TEMPERATURE = "0.7"
AZURE_OPENAI_TOP_P = "1"

def load_prompts():
    prompt_dir = Path("Prompts")

    # Load prompts from files, in order, so that static orchestration can use it as-is. In python 3.7+, the order of dictionary items is guaranteed preserved.
    prompts = {name: (prompt_dir / filename).read_text() for name, filename in {
        "content_ideator": "ContentIdeatorPrompt.txt",
        "content_expander": "ContentExpanderPrompt.txt",
        "knowledge_finder": "KnowledgeFinderPrompt.txt",
        "peer_reviewer": "PeerReviewerPrompt.txt",
        "search_optimizer": "SearchOptimizerPrompt.txt",
        "proofreader": "ProofreaderPrompt.txt",
        "summarizer": "SummarizerPrompt.txt",
        "orchestrator": "OrchestratorPrompt.txt"
    }.items()}

    return prompts

def load_llm():
    # This will change the API base to the custom URL provided by CMH, since langchain depends upon openai
    openai.api_base = AZURE_OPENAI_ENDPOINT
    openai.api_version = AZURE_OPENAI_PREVIEW_API_VERSION

    llm = ChatOpenAI(temperature=1, # There is a (possible bug?) problem that only lets me set the temperature to 1.
                 top_p=AZURE_OPENAI_TOP_P,
                 model_name=AZURE_OPENAI_MODEL_NAME,
                 api_key=AZURE_OPENAI_KEY)

    return llm

def load_agents(llm, prompts):
    agents = {}
    for name, prompt in prompts.items():
        if name != "orchestrator":
            def tool_func(input_data, prompt=prompt):
                return (PromptTemplate.from_template(prompt) | llm).invoke(input_data)

            agents[name] = Tool(
                name=name,
                func=partial(tool_func),
                description=f"{name} agent"
            )
    return agents


def static_orchestration(objective, agents):
    whitepaper = "Whitepaper failed to generate."
    current_output = objective
    for agent_tool in agents.values():
        current_output = agent_tool.func({"input": current_output}).content
        #print(f"{agent_tool.name}: {current_output}")
        if agent_tool.name == "proofreader":
            whitepaper = current_output
    return current_output, whitepaper # The "current output" is the summary, and we will also return the whitepaper

def dynamic_orchestration(objective, orchestrator_tool, agents):
    # Define agent descriptions to pass to the Orchestrator
    agent_descriptions = {
        "content_ideator": "Generates creative outlines and ideas based on the objective.",
        "content_expander": "Expands outlines into detailed and coherent content.",
        "knowledge_finder": "Finds supporting data and trends to substantiate the content.",
        "peer_reviewer": "Reviews content for accuracy and coherence.",
        "search_optimizer": "Optimizes content for SEO and online discoverability.",
        "proofreader": "Polishes content for grammar, style, and clarity.",
        "summarizer": "Summarizes detailed content into concise executive summaries." # It's possible it is more pragmatic to remove summarizer as an option.
    }

    task_context = {
        "objective": objective,
        "completed_tasks": [],
        "current_output": None,
    }
    whitepaper = "Whitepaper failed to generate."
    summary = "Summary failed to generate."
    remaining_agents = set(agents.keys())

    formatted_agent_descriptions = " ".join(
        f"{agent}: {description}" for agent, description in agent_descriptions.items()
    )

    while True:
        orchestrator_input = {
            "objective": task_context["objective"],
            "current_output": task_context["current_output"] or "No progress has been made yet.",
            "completed_tasks": ", ".join(task_context["completed_tasks"]),
            "remaining_agents": ", ".join(remaining_agents),
            "agent_descriptions": formatted_agent_descriptions,
        }

        print(f"Orchestrator Input:\n{orchestrator_input}\n")  # Debugging: Log input to Orchestrator

        orchestrator_response = orchestrator_tool.func(**orchestrator_input)

        print(f"Orchestrator Response:\n{orchestrator_response}\n")

        # Safety check: Handle "Task Complete" with unused agents
        if "Task Complete" in orchestrator_response.content:
            if remaining_agents:
                print(f"Orchestrator prematurely declared 'Task Complete'. Assigning an unused agent: {next(iter(remaining_agents))}")
                next_agent_name = next(iter(remaining_agents))  # Assign one of the unused agents
                agent_input = "Automatically assigned by system to ensure completion."  # Default input
            else:
                break
        else:
            # Parse Orchestrator's decision
            lines = orchestrator_response.content.splitlines()
            next_agent_name = None
            agent_input = []
            inside_input_tag = False

            for line in lines:
                line = line.strip()
                if line.startswith("<NEXT_AGENT>") and line.endswith("</NEXT_AGENT>"):
                    next_agent_name = line[len("<NEXT_AGENT>"): -len("</NEXT_AGENT>")].strip()
                elif line.startswith("<INPUT>"):
                    inside_input_tag = True
                    agent_input.append(line[len("<INPUT>"):].strip())
                elif line.endswith("</INPUT>"):
                    inside_input_tag = False
                    agent_input.append(line[: -len("</INPUT>")].strip())
                elif inside_input_tag:
                    agent_input.append(line)

            # Join multiline input into a single string
            agent_input = "\n".join(agent_input).strip()

        # Ensure that there is a next task to do
        if not next_agent_name or not agent_input:
            raise ValueError("Orchestrator response does not specify the next agent or input.")

        # Execute the selected agent
        if next_agent_name in agents:
            agent_tool = agents[next_agent_name]
            task_context["current_output"] = agent_tool.func({"input": agent_input}).content
            task_context["completed_tasks"].append(next_agent_name)
            remaining_agents.discard(next_agent_name)

            # Proofreader and summarizer outputs are what we will ultimately return
            if next_agent_name == "proofreader":
                whitepaper = task_context["current_output"]
            elif next_agent_name == "summarizer":
                summary = task_context["current_output"]

    return summary, whitepaper

def static_approach():
    llm = load_llm()
    prompts = load_prompts()
    agents = load_agents(llm, prompts)
    objective = Path("input.txt").read_text().strip()
    if not objective:
        raise ValueError("The input.txt file is empty. Please provide a valid objective.")

    summary, whitepaper = static_orchestration(objective, agents)
    summary_file_path = Path("Output") / "StaticSummary.md"
    whitepaper_file_path = Path("Output") / "StaticWhitepaper.md"

    with open(summary_file_path, "w", encoding="utf-8") as summary_file:
        summary_file.write(summary)

    with open(whitepaper_file_path, "w", encoding="utf-8") as whitepaper_file:
        whitepaper_file.write(whitepaper)

def create_orchestrator_tool(prompt, llm):
    def orchestrator_tool_func_wrapped(objective, current_output, completed_tasks, remaining_agents, agent_descriptions):
        input_data = {
            "objective": objective,
            "current_output": current_output,
            "completed_tasks": completed_tasks,
            "remaining_agents": remaining_agents,
            "agent_descriptions": agent_descriptions
        }
        print(f"Rendered Prompt for {current_output}:\n{PromptTemplate.from_template(prompt).format(**input_data)}\n")
        return (PromptTemplate.from_template(prompt) | llm).invoke(input_data)

    return StructuredTool.from_function(
        orchestrator_tool_func_wrapped,
        name="orchestrator",
        description="Orchestrator agent",
        schema={
            "objective": str,
            "current_output": str,
            "completed_tasks": str,
            "remaining_agents": str,
            "agent_descriptions": str
        }
    )

def dynamic_approach():
    llm = load_llm() # Although this violates DRY, the code will be more confusing/unreadable with the alternative
    prompts = load_prompts()
    agents = load_agents(llm, prompts)
    objective = Path("input.txt").read_text().strip()
    if not objective:
        raise ValueError("The input.txt file is empty. Please provide a valid objective.")

    orchestrator_prompt = prompts["orchestrator"]

    # Define the orchestrator using StructuredTool
    orchestrator_tool = create_orchestrator_tool(orchestrator_prompt, llm)

    summary, whitepaper = dynamic_orchestration(objective, orchestrator_tool, agents)
    summary_file_path = Path("Output") / "DynamicSummary.md"
    whitepaper_file_path = Path("Output") / "DynamicWhitepaper.md"

    with open(summary_file_path, "w", encoding="utf-8") as summary_file:
        summary_file.write(summary)

    with open(whitepaper_file_path, "w", encoding="utf-8") as whitepaper_file:
        whitepaper_file.write(whitepaper)

if __name__ == "__main__":
    static_approach()
    dynamic_approach()