"""Hierarchical CrewAI workflow using tools discovered directly from MCP."""

import os
import sys
from pathlib import Path

os.environ.setdefault(
    "CREWAI_STORAGE_DIR", str(Path(__file__).with_name(".crewai_storage"))
)

import streamlit as st
from crewai import Agent, Crew, LLM, Process, Task
from crewai_tools import MCPServerAdapter
from dotenv import load_dotenv
from mcp import StdioServerParameters


load_dotenv(Path(__file__).with_name(".env"))

def create_hierarchical_crew(mcp_tools: list) -> Crew:
    """Create the hierarchical crew with tools supplied by the MCP adapter."""
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise RuntimeError("GOOGLE_API_KEY is missing from the environment.")

    llm = LLM(model="gemini/gemini-3.1-flash-lite", api_key=google_api_key)

    researcher = Agent(
        role="Web Research Specialist",
        goal="Find accurate, current, source-backed information for the requested blog.",
        backstory="You research topics carefully and summarize sources clearly.",
        tools=mcp_tools,
        llm=llm,
        verbose=False,
    )
    writer = Agent(
        role="Markdown Blog Writer",
        goal="Turn research into a useful, beginner-friendly Markdown blog.",
        backstory="You write clear articles with headings, citations, and practical structure.",
        tools=mcp_tools,
        llm=llm,
        verbose=False,
    )
    manager = Agent(
        role="Editorial Manager",
        goal="Coordinate research and writing into a polished final blog file.",
        backstory="You delegate work, review outputs, and ensure the final deliverable is complete.",
        llm=llm,
        verbose=False,
    )

    research_task = Task(
        description="Research the topic {topic} with the web_search tool. Return concise notes and source URLs.",
        expected_output="Source-backed research notes.",
        agent=researcher,
    )
    writing_task = Task(
        description=(
            "Using the research, write a complete Markdown blog with an introduction, "
            "useful sections, conclusion, and source links. Then use write_blog_markdown "
            "to save it to {file_path}."
        ),
        expected_output="A completed Markdown blog and confirmation of the saved file.",
        agent=writer,
        context=[research_task],
    )

    return Crew(
        agents=[researcher, writer],
        tasks=[research_task, writing_task],
        process=Process.hierarchical,
        manager_agent=manager,
        memory=True,
        verbose=False,
    )

def run(topic: str, file_path: str = "blog.md") -> str:
    """Start the MCP server through CrewAI, run the crew, and close the server."""
    server_params = StdioServerParameters(
        command = sys.executable,
        args=[str(Path(__file__).with_name("mcp_server.py"))],
        env=dict(os.environ),
    )
    with MCPServerAdapter(server_params) as mcp_tools:
        result = create_hierarchical_crew(mcp_tools).kickoff(
            inputs = {"topic": topic, "file_path": file_path}
        )
    return str(result)

def run_streamlit_app() -> None:
    """Display the hierarchical MCP workflow in a chat-style UI."""
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

        with st.chat_message("assistant"):
            with st.spinner("Researching and writing your answer..."):
                try:
                    answer = run(prompt, "blog.md")
                except Exception as error:
                    answer = f"Sorry, I couldn't complete that request: {error}"
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__" and st.runtime.exists():
    run_streamlit_app()