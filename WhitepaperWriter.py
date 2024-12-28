from pathlib import Path
from langchain.agents import Tool, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.llms import OpenAI

def load_prompts():
    # Define the folder containing your prompts
    prompt_dir = Path("/Prompts")

    # Load prompts from files
    prompts = {name: (prompt_dir / filename).read_text() for name, filename in {
        "search_optimizer": "SearchOptimizerPrompt.txt",
        "content_ideator": "ContentIdeatorPrompt.txt",
        "peer_reviewer": "PeerReviewerPrompt.txt",
        "proofreader": "ProofreaderPrompt.txt",
        "knowledge_finder": "KnowledgeFinderPrompt.txt",
        "summarizer": "SummarizerPrompt.txt",
        "content_expander": "ContentExpanderPrompt.txt",
        "orchestrator": "OrchestratorPrompt.txt"
    }.items()}

    return prompts

def static_approach():
    prompts = load_prompts()
    pass