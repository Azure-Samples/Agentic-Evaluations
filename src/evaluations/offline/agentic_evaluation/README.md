# Evaluation of Agentic Systems using Azure AI Foundry

Agents are AI models with memories that communicate via messages. They can interact with themselves, other agents, or the human user, these messages include text, multimodalities, and tools or function calls, forming a chat history/thread/trajectory.

Agentic systems can range from single agents with tool calling to complex multi-agent systems that communicate to complete tasks. Building an evaluation pipeline for such systems starts with creating ground truth datasets based on real-world usage. 

This framework provides a step-by-step approch to building a pipeline to Evaluate agentic system using Azure AI Foundry, using single agent with multiple plugins from Sematic Kernel as an example. This repository provides a reporting framework using html report locally to analyze, visualize and share the evaluation results to various stake holders. 
