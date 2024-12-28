import openai
from pathlib import Path
from langchain.agents import Tool
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from functools import partial
import os

AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_ENDPOINT = "https://openai-cmh-eastus2.openai.azure.com/"
AZURE_OPENAI_MODEL_NAME = "o1-preview" # Note: we might not want to be using a chat model for this task.
AZURE_OPENAI_MODEL = "cmh-eastus2-o1-preview"
AZURE_OPENAI_PREVIEW_API_VERSION = "2024-09-01-preview"
AZURE_OPENAI_TEMPERATURE = "0.7"
AZURE_OPENAI_TOP_P = "1"

def load_prompts():
    # Define the folder containing your prompts
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

    #TODO: May need to use "AZURE_OPENAI_MODEL" instead/in tandem

    llm = ChatOpenAI(temperature=1, # There is a (possible bug?) problem that only lets me set the temperature to 1.
                 top_p=AZURE_OPENAI_TOP_P,
                 model_name=AZURE_OPENAI_MODEL_NAME,
                 api_key=AZURE_OPENAI_KEY)

    return llm

def load_agents(llm, prompts):
    agents = {}
    for name, prompt in prompts.items():
        if name != "orchestrator":
            def tool_func(input_data, prompt=prompt, name=name):
                # For debugging purposes, allow us to print the entire input to the LLM
                rendered_prompt = PromptTemplate.from_template(prompt).format(**input_data)
                print(f"Rendered Prompt for {name}:\n{rendered_prompt}\n")  # Debugging: Logs the exact prompt sent to the LLM
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
        print(f"{agent_tool.name}: {current_output}")
        if agent_tool.name == "proofreader":
            whitepaper = current_output
    return current_output, whitepaper # The "current output" is the summary, and we will also return the whitepaper

def dynamic_orchestration(objective, orchestrator_chain, agents):
    #TODO: Implement
    pass

def static_approach():
    llm = load_llm()
    prompts = load_prompts()
    agents = load_agents(llm, prompts)
    objective = Path("input.txt").read_text().strip()
    if not objective:
        raise ValueError("The input.txt file is empty. Please provide a valid objective.")

    summary, whitepaper = static_orchestration(objective, agents)
    summary_file_path = Path("Output") / "StaticSummary.txt"
    whitepaper_file_path = Path("Output") / "StaticWhitepaper.txt"

    with open(summary_file_path, "w", encoding="utf-8") as summary_file:
        summary_file.write(summary)

    with open(whitepaper_file_path, "w", encoding="utf-8") as whitepaper_file:
        whitepaper_file.write(whitepaper)

def dynamic_approach():
    llm = load_llm() # Although this violates DRY, the code will be more confusing/unreadable with the alternative
    prompts = load_prompts()
    agents = load_agents(llm, prompts)
    objective = Path("input.txt").read_text().strip()
    if not objective:
        raise ValueError("The input.txt file is empty. Please provide a valid objective.")

    orchestrator_prompt = prompts["orchestrator"]
    orchestrator_chain = LLMChain(llm=llm, prompt=PromptTemplate.from_template(orchestrator_prompt))

    summary, whitepaper = dynamic_orchestration(objective, orchestrator_chain, agents)
    summary_file_path = Path("Output") / "DynamicSummary.txt"
    whitepaper_file_path = Path("Output") / "DynamicWhitepaper.txt"

    with open(summary_file_path, "w", encoding="utf-8") as summary_file:
        summary_file.write(summary)

    with open(whitepaper_file_path, "w", encoding="utf-8") as whitepaper_file:
        whitepaper_file.write(whitepaper)

if __name__ == "__main__":
    static_approach()