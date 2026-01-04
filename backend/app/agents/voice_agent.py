"""
LangGraph Agent with Gemini integration.

This is the core orchestration logic that:
1. Receives user messages
2. Decides which tools to use
3. Executes tools
4. Returns responses
"""
from typing import TypedDict, Annotated, Sequence
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage

import logging

from app.config import get_settings, set_session_context
from app.tools.gemini_web_search import get_gemini_web_search_tool
from app.tools.rag_search import get_rag_search_tool
from app.tools.document_info import get_document_info_tool
from app.tools.note_taking import get_note_taking_tool, get_note_retrieval_tool, get_note_edit_tool, get_note_list_tool
from app.tools.command_execution import get_command_execution_tool, get_system_info_tool

logger = logging.getLogger(__name__)
settings = get_settings()


# ============================================================================
# Agent State Definition
# ============================================================================

class AgentState(TypedDict):
    """
    State of the agent throughout the conversation.

    Attributes:
        messages: List of all messages in the conversation
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]


# ============================================================================
# Agent Components
# ============================================================================

class VoiceAgent:
    """
    LangGraph-powered Voice Assistant Agent.

    Uses Gemini 2.5 Flash for reasoning and tool calling.
    """

    def __init__(self):
        """Initialize the agent with tools and LLM."""
        logger.info("Initializing Voice Agent...")

        # Initialize LLM with function calling
        self.llm = ChatGoogleGenerativeAI(
            model=settings.LLM_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
        )

        # Initialize tools
        self.tools = self._setup_tools()

        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # Build the graph
        self.graph = self._build_graph()

        logger.info(f"✅ Agent initialized with {len(self.tools)} tools")

    def _setup_tools(self):
        """
        Set up all available tools.

        Tools included:
        1. web_search (Gemini + Google Search Grounding) - ALL web searches (time, weather, news, facts, research, etc.)
        2. rag_search - Search uploaded documents (knowledge base)
        3. check_available_documents - Check what documents are in knowledge base
        4. list_notes - List all available notes
        5. save_note - Save notes to database and files
        6. retrieve_note - Retrieve saved notes
        7. edit_note - Edit or append to existing notes
        8. execute_command - Execute safe local system commands
        9. get_system_info - Get local system information
        """
        tools = [
            # Search tools
            get_gemini_web_search_tool(),   # Universal web search with Google Search grounding
            get_rag_search_tool(),          # Uploaded documents search
            get_document_info_tool(),       # Check available documents

            # Note tools
            get_note_list_tool(),           # List all notes
            get_note_taking_tool(),         # Create new notes
            get_note_retrieval_tool(),      # Find/read notes
            get_note_edit_tool(),           # Edit existing notes

            # System tools
            get_command_execution_tool(),   # Execute whitelisted commands
            get_system_info_tool(),         # Get system information
        ]
        return tools

    def _build_graph(self):
        """
        Build the LangGraph workflow.

        The graph follows this flow:
        1. User input → Agent (decide what to do)
        2. Agent → Tools (if tool needed) → Agent (process results)
        3. Agent → End (return final response)
        """
        # Create the graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("agent", self._call_agent)
        workflow.add_node("tools", ToolNode(self.tools))

        # Set entry point
        workflow.set_entry_point("agent")

        # Add conditional edges
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",  # If agent wants to use tools
                "end": END  # If agent has final answer
            }
        )

        # Add edge from tools back to agent
        workflow.add_edge("tools", "agent")

        # Compile the graph
        return workflow.compile()

    def _call_agent(self, state: AgentState):
        """
        Agent decision node.

        Decides whether to:
        - Use a tool
        - Return final response
        """
        messages = state["messages"]

        # Invoke LLM with tools
        response = self.llm_with_tools.invoke(messages)

        # Return updated state
        return {"messages": [response]}

    def _should_continue(self, state: AgentState):
        """
        Determine if agent should continue to tools or end.

        Returns:
            "continue" if agent wants to use tools
            "end" if agent has final response
        """
        messages = state["messages"]
        last_message = messages[-1]

        # If there are tool calls, continue to tools
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            logger.info(f"Agent calling tools: {[tc['name'] for tc in last_message.tool_calls]}")
            return "continue"

        # Otherwise, we're done
        logger.info("Agent has final response")
        return "end"

    def chat(self, message: str, session_id: str = "default", conversation_history: list = None) -> dict:
        """
        Send a message to the agent and get response.

        Args:
            message: User's message
            session_id: Session identifier for conversation tracking
            conversation_history: List of previous messages in format [{"role": "user/assistant", "message": "..."}]

        Returns:
            Dictionary with response and metadata
        """
        try:
            # Set session context for tools to access
            set_session_context(session_id)

            logger.info(f"[Session: {session_id}] User: {message}")

            # Build message history
            messages = []

            # Add initial system prompt for guidance

            # Check if any documents were uploaded in this session
            has_uploaded_docs = False
            if conversation_history:
                for msg in conversation_history:
                    if msg["role"] == "system" and "Document uploaded" in msg.get("message", ""):
                        has_uploaded_docs = True
                        break

            if has_uploaded_docs:
                system_prompt = (
                    "You are a helpful AI assistant with access to multiple tools. "
                    "IMPORTANT CONTEXT RULES:\n"
                    "1. ONLY answer the CURRENT user question - do NOT reference previous unrelated queries\n"
                    "2. REMEMBER context about: uploaded documents, saved notes, file/directory operations, ongoing conversations\n"
                    "3. When user says 'it', 'that file', 'the folder', 'that document' - refer to conversation history to identify what they mean\n"
                    "4. If user asks about a file/folder mentioned earlier, remember which one they're referring to\n"
                    "5. For UNRELATED new questions (time, weather, general facts), give fresh responses without referencing old queries\n\n"
                    "CONTEXTUAL REFERENCE TRACKING:\n"
                    "- ALWAYS maintain awareness of files, folders, documents, and notes mentioned in conversation history\n"
                    "- When user uses pronouns (it, that, this, those) or vague references, LOOK BACK at the conversation\n"
                    "- Track what was discussed: 'the document' = last mentioned document, 'that note' = last mentioned note\n"
                    "- Examples:\n"
                    "  * User: 'I uploaded a file about AI' → Later: 'What does it say?' → 'it' = the AI file\n"
                    "  * User: 'I saved a note called Ideas' → Later: 'Add X to it' → 'it' = Ideas note\n"
                    "  * User: 'Created folder /docs' → Later: 'List files in that folder' → 'that folder' = /docs\n"
                    "- Check system messages in history for uploads, note creation, and file operations\n"
                    "- If unclear what user is referring to, ask for clarification instead of guessing\n\n"
                    "WEB SEARCH QUERY FORMULATION (CRITICAL):\n"
                    "When using web_search tool, PRESERVE ALL user intent and details:\n"
                    "- DO NOT simplify or paraphrase - maintain exact product names, versions, specifications\n"
                    "- INCLUDE source requirements: 'official site', 'brand website', 'go to X' → search for 'X official site'\n"
                    "- KEEP all qualifiers: 'current', 'latest', 'today', specific locations\n"
                    "- NEVER change product names (conditioner ≠ shampoo, iPhone 15 ≠ iPhone 14)\n"
                    "- Examples:\n"
                    "  ✓ User: 'Go to Nike site for price' → Query: 'Nike official website price'\n"
                    "  ✓ User: 'True Frog conditioner MRP from brand site' → Query: 'True Frog official brand site conditioner MRP'\n"
                    "  ✗ User: 'conditioner' → Query: 'shampoo' (WRONG - never change products!)\n"
                    "  ✗ User: 'brand site' → Query: drops this requirement (WRONG - keep source info!)\n\n"
                    "DOCUMENT SEARCH: Documents have been uploaded in this session. "
                    "When user asks questions about topics that could be in uploaded documents, "
                    "use 'rag_search' FIRST. Only use web search if rag_search returns no results.\n\n"
                    "NOTE EDITING WORKFLOW: When user asks to edit/add to a note: "
                    "(1) Use 'list_notes', (2) Identify note, (3) Use 'retrieve_note', "
                    "(4) Ask what to add, (5) Wait for content, (6) Use 'edit_note'."
                )
                logger.info(f"[Session: {session_id}] Documents detected in session - prioritizing RAG search")
            else:
                system_prompt = (
                    "You are a helpful AI assistant with access to multiple tools. "
                    "IMPORTANT CONTEXT RULES:\n"
                    "1. ONLY answer the CURRENT user question - do NOT reference previous unrelated queries\n"
                    "2. REMEMBER context about: saved notes, file/directory operations, ongoing conversations\n"
                    "3. When user says 'it', 'that file', 'the folder', 'that note' - refer to conversation history to identify what they mean\n"
                    "4. If user asks about a file/folder/note mentioned earlier, remember which one they're referring to\n"
                    "5. For UNRELATED new questions (time, weather, general facts), give fresh responses without referencing old queries\n\n"
                    "CONTEXTUAL REFERENCE TRACKING:\n"
                    "- ALWAYS maintain awareness of files, folders, documents, and notes mentioned in conversation history\n"
                    "- When user uses pronouns (it, that, this, those) or vague references, LOOK BACK at the conversation\n"
                    "- Track what was discussed: 'the document' = last mentioned document, 'that note' = last mentioned note\n"
                    "- Examples:\n"
                    "  * User: 'I uploaded a file about AI' → Later: 'What does it say?' → 'it' = the AI file\n"
                    "  * User: 'I saved a note called Ideas' → Later: 'Add X to it' → 'it' = Ideas note\n"
                    "  * User: 'Created folder /docs' → Later: 'List files in that folder' → 'that folder' = /docs\n"
                    "- Check system messages in history for uploads, note creation, and file operations\n"
                    "- If unclear what user is referring to, ask for clarification instead of guessing\n\n"
                    "WEB SEARCH QUERY FORMULATION (CRITICAL):\n"
                    "When using web_search tool, PRESERVE ALL user intent and details:\n"
                    "- DO NOT simplify or paraphrase - maintain exact product names, versions, specifications\n"
                    "- INCLUDE source requirements: 'official site', 'brand website', 'go to X' → search for 'X official site'\n"
                    "- KEEP all qualifiers: 'current', 'latest', 'today', specific locations\n"
                    "- NEVER change product names (conditioner ≠ shampoo, iPhone 15 ≠ iPhone 14)\n"
                    "- Examples:\n"
                    "  ✓ User: 'Go to Nike site for price' → Query: 'Nike official website price'\n"
                    "  ✓ User: 'True Frog conditioner MRP from brand site' → Query: 'True Frog official brand site conditioner MRP'\n"
                    "  ✗ User: 'conditioner' → Query: 'shampoo' (WRONG - never change products!)\n"
                    "  ✗ User: 'brand site' → Query: drops this requirement (WRONG - keep source info!)\n\n"
                    "NOTE EDITING WORKFLOW: When user asks to edit/add to a note: "
                    "(1) Use 'list_notes', (2) Identify note, (3) Use 'retrieve_note', "
                    "(4) Ask what to add, (5) Wait for content, (6) Use 'edit_note'."
                )

            # Collect system messages from conversation history to incorporate into main system prompt
            system_context_parts = []
            uploaded_documents = []  # Track uploaded document filenames in THIS session

            if conversation_history:
                for msg in conversation_history:
                    if msg["role"] == "system":
                        # Extract system messages and add to context
                        system_context_parts.append(msg["message"])

                        # Extract document filenames from upload messages
                        if "Document uploaded:" in msg["message"]:
                            # Extract filename from message like: "[SYSTEM] Document uploaded: 'filename.pdf' (6 chunks)."
                            try:
                                start = msg["message"].find("'") + 1
                                end = msg["message"].find("'", start)
                                if start > 0 and end > start:
                                    doc_name = msg["message"][start:end]
                                    uploaded_documents.append(doc_name)
                                    logger.info(f"[Session: {session_id}] Extracted document name: {doc_name}")
                            except:
                                pass

            # If we have system context from history, append it to the main system prompt
            if system_context_parts:
                system_prompt += "\n\n" + "CONTEXT FROM CONVERSATION:\n" + "\n".join(system_context_parts)
                logger.info(f"[Session: {session_id}] Added {len(system_context_parts)} system context messages to prompt")

            # If documents were uploaded in this session, add explicit reference
            if uploaded_documents:
                doc_list = "', '".join(uploaded_documents)
                system_prompt += (
                    f"\n\nDOCUMENTS UPLOADED IN THIS SESSION:\n"
                    f"The following document(s) were uploaded in THIS conversation session: '{doc_list}'\n"
                    f"When user says 'the document', 'the file', 'the paper', or 'it', they are referring to: '{uploaded_documents[-1]}'\n"
                    f"IMPORTANT: When searching with rag_search, focus on content from THIS document: '{uploaded_documents[-1]}'\n"
                    f"If search results come from other documents (not '{uploaded_documents[-1]}'), mention this to the user and ask for clarification.\n"
                )
                logger.info(f"[Session: {session_id}] Added {len(uploaded_documents)} document references to prompt")

            # Add the consolidated system message (only one system message allowed by Gemini)
            messages.append(SystemMessage(content=system_prompt))

            # Add conversation history if provided (skip system messages as they're now in the main prompt)
            if conversation_history:
                for msg in conversation_history:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["message"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["message"]))
                    # Skip system messages - they're already in the main system prompt above
                logger.info(f"[Session: {session_id}] Loaded {len(conversation_history)} previous messages")

            # Add current user message
            messages.append(HumanMessage(content=message))

            # Create initial state
            initial_state = {
                "messages": messages
            }

            # Run the graph
            result = self.graph.invoke(initial_state)

            # Extract final response
            final_message = result["messages"][-1]

            # Get tools used (if any)
            tools_used = []
            for msg in result["messages"]:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    tools_used.extend([tc["name"] for tc in msg.tool_calls])

            response_text = final_message.content

            logger.info(f"[Session: {session_id}] Assistant: {response_text[:100]}...")
            if tools_used:
                logger.info(f"[Session: {session_id}] Tools used: {tools_used}")

            return {
                "response": response_text,
                "tools_used": list(set(tools_used)),  # Remove duplicates
                "session_id": session_id
            }

        except Exception as e:
            logger.error(f"Error in agent chat: {str(e)}", exc_info=True)
            return {
                "response": f"I encountered an error: {str(e)}. Please try again.",
                "tools_used": [],
                "session_id": session_id
            }


# ============================================================================
# Agent Factory
# ============================================================================

_agent_instance = None


def get_agent() -> VoiceAgent:
    """
    Get or create the agent instance (singleton pattern).

    Returns:
        VoiceAgent instance
    """
    global _agent_instance

    if _agent_instance is None:
        _agent_instance = VoiceAgent()

    return _agent_instance
