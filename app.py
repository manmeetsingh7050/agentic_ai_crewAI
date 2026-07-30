"""Generate a beginner-friendly Artificial Intelligence blog with CrewAI."""

import os
from pathlib import Path

from crewai import Agent, Crew, LLM, Process, Task
from dotenv import load_dotenv
import streamlit as st


load_dotenv(Path(__file__).with_name(".env"))

CHAT_HISTORY = """
User: Hi, I want to learn Artificial Intelligence.

Assistant: Great! Artificial Intelligence is a branch of computer science
that enables machines to perform tasks that normally require human intelligence.

User: Can you also explain current trends?
"""


def create_crew() -> Crew:
    """Create the sequential research-and-writing crew."""
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is missing. Add it to .env before running this app."
        )

    llm = LLM(
        model="gemini/gemini-3.5-flash-lite",
        api_key=google_api_key,
    )

    research_agent = Agent(
        role="AI Researcher",
        goal="Find useful information about the given topic.",
        backstory=(
            "You are an expert AI researcher who gathers accurate and "
            "well-structured information."
        ),
        llm=llm,
        verbose=False,
    )

    writer_agent = Agent(
        role="Technical Blog Writer",
        goal="Write beginner-friendly technical blogs.",
        backstory="You convert technical research into simple and engaging articles.",
        llm=llm,
        verbose=False,
    )

    research_task = Task(
        description="""
Previous Conversation:

{chat_history}

Research the topic: Artificial Intelligence

Collect:
- Definition
- Latest Trends
- Applications
- Future Scope

Use the previous conversation whenever relevant.
Return detailed research notes.
""",
        expected_output="Detailed research notes",
        agent=research_agent,
    )

    writing_task = Task(
        description="""
Previous Conversation:

{chat_history}

Using the research notes from the previous task, write a beginner-friendly blog.

Include:
- Introduction
- Latest Trends
- Applications
- Future Scope
- Conclusion

If the user's previous conversation indicates any preferences, adapt the writing accordingly.
""",
        expected_output="Complete blog article",
        agent=writer_agent,
    )

    return Crew(
        agents=[research_agent, writer_agent],
        tasks=[research_task, writing_task],
        process=Process.sequential,
        memory=True,
        verbose=False,
    )


def run_crew(chat_history: str = CHAT_HISTORY) -> str:
    """Run the existing CrewAI workflow with the supplied conversation."""
    result = create_crew().kickoff(inputs={"chat_history": chat_history})
    return str(result)


def main() -> None:
    result = run_crew()
    print("\n================ FINAL OUTPUT ================\n")
    print(result)


def run_streamlit_app() -> None:
    """Display the CrewAI workflow in a simple chat interface."""
    st.set_page_config(page_title="AI Learning Assistant", page_icon="🤖")
    st.title("🤖 AI Learning Assistant")
    st.caption("Ask a question about Artificial Intelligence and get a beginner-friendly answer.")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hi! What would you like to learn about Artificial Intelligence?",
            }
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask about Artificial Intelligence..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        chat_history = "\n\n".join(
            f"{'User' if message['role'] == 'user' else 'Assistant'}: {message['content']}"
            for message in st.session_state.messages
        )
        with st.chat_message("assistant"):
            with st.spinner("Researching and writing your answer..."):
                try:
                    answer = run_crew(chat_history)
                except Exception as error:
                    answer = f"Sorry, I couldn't complete that request: {error}"
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    if st.runtime.exists():
        run_streamlit_app()
    else:
        main()
