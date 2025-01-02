To run WhitepaperWriter, you will need to set your AZURE_OPENAI_KEY environment variable, as well as install necessary packages using pip.

Development Notes:

- For my static approach, I figured that SEO optimization should happen before proofreading, but after peer reviewing. Depending on how important SEO is, it can be placed at a different step in the process.
- I wasn't able to get the API to accept a custom temperature. I believe this is a quirk with the custom Azure deployment.
- The model provided is a chat model, but it is worth considering using a non-chat model. Non-chat models may be more cost efficient for very similar performance. If cost were an important consideration, then this option should be investigated.
- In the dynamic approach, there are several simplifications that can be done that would likely improve performance. However, I wanted to hand as much work over to the Orchestrator as possible, so that can test its limits and demonstrate potential for usage in a much more complex scenario.
- A decent chunk of code is duplicated between the dynamic and static approaches, I left it this way for overall conciseness as splitting those things into their own functions seems to add unnecessary complexity.
- Variables could be renamed for better readability. This could be better informed by how this program would be utilized in the future (what sorts of ideas will we be feeding it?).
- Refactoring the code into several different files may be a good idea. Additionally, a significantly more object-oriented structure could help in the case that this program will continue to be developed and extended for other use cases.
- Some people consider using "while True" to be stylistically controversial. It could be refactored out.

Prompt/Agent Notes:

- "Brainstorming Agent" to start things off? Split up Ideator into two
- Should we be introduce an agent that specifically trims and/or reorders content for better logical flow? "Peer reviewing" seems like a separate task.
- My general strategy with the prompts was to be a bit more specific in what I am asking for. A lot of the language is quite nebulous. There's still further progress to be made on that.
- There were several references to the audience in these prompts. I don't think the agents have access to that information, currently. I edited them accordingly. This could be a potential future feature that also factors into the SEO'd/Summarized dichotomy.
- An approach that may benefit the output, but would increase the cost as well as complexity, is to add a more "conversational" flow to the agents rather than a simple input/output. Such a flow would justify a chat model being used. An example of this would be the Peer Reviewer: It gets fed the content to review, it replies with its suggested edits, and then another agent applies those edits. As my current approach doesn't use "suggestions", I am aiming to remove references to that.
- It's important that agents are properly equipped to handle the tasks given, and we should not be asking them to do things that they are not capable of. Preventing plagairism, for instance, may be outside the wheelhouse of these agents, without a custom tool made to intentionally achieve this purpose.
- We need to make sure the scope of what we are asking the agents is limited so that each agent has one purpose. Overlapping responsibilities can cause the output to be unnecessarily verbose or not reader friendly.
- Adding in a web search agent could be very helpful, especially in conjunction with the
- For a test prompt such as this, it may be nice to have a professionally written whitepaper to judge against, or even several. Then, there could be a much more objective way of judging the success of specific changes.
- The quality of output may benefit massively from changes to the agent prompts. In a real-world scenario where the quality of result has a high financial impact, A/B testing with many iterations may be wise. It may be worth hiring someone specifically for that purpose.