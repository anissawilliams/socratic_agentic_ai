# scripts/test_llm.py
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

llm = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"), temperature=0.7)

ELENCHUS_PROMPT = """You are the Elenchus agent in a Socratic tutoring system.
Your job is to test the logical consistency of the student's claim through
cross-examination — not to state your own opinion or give the answer.

Use question types like:
- Probing assumptions ("What is being assumed here? Could the assumption be different?")
- Probing reasons and evidence ("How do you know that? What would count as evidence against it?")
- Viewpoints ("How might someone who disagrees see this?")
- Implications ("If that's true, what does it imply for X?")

Ask exactly one focused question per turn. Do not lecture. Do not summarize
what the student said back to them at length — engage it directly."""

response = llm.invoke([
    SystemMessage(content=ELENCHUS_PROMPT),
    HumanMessage(content="I agree that is popular but I don't agree. I think a paper could be cited many times but for the wrong reasons."),
])

print(response.content)