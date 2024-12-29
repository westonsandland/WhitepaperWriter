Develpoment Notes:

- For my static approach, I figured that SEO optimization should happen before proofreading, but after peer reviewing. Depending on how important SEO is, it can be placed at a different step in the process.
- I wasn't able to get the API to accept a custom temperature. I believe this is a quirk with the custom endpoint.
- The model provided is a chat model, but it is worth considering using a non-chat model. Non-chat models may be more cost efficient for very similar performance. If cost were an important consideration, then this option should definitely be investigated.
- I didn't end up needing to use "AZURE_OPENAI_MODEL".
- In the dynamic approach, there are several simplifications that can be done that would likely improve performance. However, I wanted to hand as much work over to the Orchestrator as possible, so that can test its limits and demonstrate potential for usage in a much more complex scenario.
- Some people consider using "while True" to be controversial when it comes to style. It could be refactored out.
- A decent chunk of code is duplicated between the dynamic and static approaches, I left it this way for overall conciseness as splitting those things into their own functions seems to add unnecessary complexity.
- Variables could be renamed for better readability. This could be better informed by how this program would be utilized in the future (what sorts of ideas will we be feeding it?).
- The quality of output may benefit massively from changes to the agent prompts. In a scenario where the quality of result has a high financial impact, A/B testing with many iterations may be wise. It may be worth hiring someone specifically for that purpose.