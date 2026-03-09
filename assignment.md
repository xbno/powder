# Lead AI Engineer Tech Assessment

## Objective

Build a simple agent that is an expert in answering questions in a field in which you are knowledgeable (Pick something that excites you!). Design and implement a solution for evaluating the performance of that agent using a traditional AI/ML/Data Science strategy.

The implementation does not have to be production ready. It must simply demonstrate how you think about building agents and using data science to improve them. Think of it as a proof of concept for an expert agent with a strategy around improving it over time.

## Requirements

- **Local execution:** Must run end-to-end on a laptop
- Agent
    - Must be a **multistep** agent
    - Must use at least 2 tools. Could be any tool of your choosing but these are some examples:
        - Web search
        - Query of local data store
        - Python function
        - API call
        - MCP call
- Evaluation
    - Must not depend **solely** on LLMs for scoring or feedback (though LLMs can assist).
    - Should show how performance could be **measured and improved** over time (e.g., metrics, datasets, error analysis).

## Deliverables

- A GitHub repo (can be private) with clear setup instructions.
- Schedule a short review session to present and discuss your design and results.

## Examples

Stylist

- Given a prompt “*What should I wear to my prom?*”
- Outcome
    - Search prom ideas
    - Pick an idea
    - Find a Suit
    - Picks shows that would work well with suit
    - Passes on full outfit to critic agent

Stock Picker

- Given a prompt “*What tech stock should I invest in?*”
- Outcome
    - Searches for a list of tech stocks using an API
    - Iterates through the list
    - Narrows down list by using a tool call (a python function that calculates a stocks alpha)
    - Searches the internet for stock sentiment
    - Returns stock pick

## **How We’ll Evaluate**

We’re not grading on polish — we’re looking for **how you think**. Specifically:

- **Reasoning & Design (35%)** – How clearly your agent breaks down tasks and uses tools to achieve its goal.
    - Multi-step implementation
    - Reasoning step
    - Tool choice
- **Evaluation Strategy (35%)** – How well you measure and analyze your agent’s performance using data or metrics.
    - Quantifiable metrics to evaluate whether the agent is improving
- **Creativity & Domain Expertise (15%)** – How interesting, relevant, or insightful your chosen domain and approach are.
- **Clarity & Simplicity (15%)** – How easy it is to understand, run, and follow your code and explanation.