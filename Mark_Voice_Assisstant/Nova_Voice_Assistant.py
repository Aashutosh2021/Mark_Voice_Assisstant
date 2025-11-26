import asyncio
import os
import time
from datetime import datetime
from typing import List, Optional
from dotenv import load_dotenv
from livekit import rtc
from livekit import agents
from livekit.agents import Agent, AgentSession, RoomInputOptions, get_job_context
from livekit.plugins import noise_cancellation, google
from livekit.agents.llm.chat_context import ChatContext

# Import prompts and tools
from prompts import (
    AGENT_INSTRUCTION,
    SESSION_INSTRUCTION,
    AGENT_INSTRUCTION_FOR_TOOLS,
    SESSION_INSTRUCTION_2
)

from tools import (
    get_weather,
    search_web,
    play_media,
    get_time_info,
    system_power_action,
    manage_window,
    desktop_control,
    list_active_windows,
    get_today_reminder_message_from_db,
    say_reminder,
    send_whatsapp_message,
    write_in_notepad,
    open_app,
    press_key,
    get_system_info,
    type_user_message_auto,
    scan_system_for_viruses,
    control_ac_bulb,
    use_smart_clipboard,
    control_system_volume,
    control_screen_brightness,
    control_microphone,
    execute_multi_task,
    analyze_groundwater_dataset,
    open_app_on_screen,
    control_media,
    generate_ai_image,
    open_file_command,
    generate_and_type_code
)

load_dotenv()

class Assistant(Agent):
    def __init__(self) -> None:
        # Set assistant instance for tools
        import tools
        tools.assistant_instance = self

        # Feature mapping for different variants
        FEATURE_MAP = {
            "core": [
                search_web,
                get_time_info,
                open_app,
                get_system_info,
                control_microphone,
            ],
            "pro": [
                search_web,
                get_time_info,
                open_app,
                get_system_info,
                system_power_action,
                get_weather,
                manage_window,
                list_active_windows,
                play_media,
                press_key,
                type_user_message_auto,
                control_microphone,
            ],
            "ultra": [
                search_web,
                get_time_info,
                open_app,
                get_system_info,
                system_power_action,
                get_weather,
                manage_window,
                list_active_windows,
                play_media,
                press_key,
                type_user_message_auto,
                desktop_control,
                scan_system_for_viruses,
                send_whatsapp_message,
                write_in_notepad,
                # control_ac_bulb,
                use_smart_clipboard,
                control_system_volume,
                control_screen_brightness,
                control_microphone,
                execute_multi_task,
                analyze_groundwater_dataset,
                open_app_on_screen,
                control_media,
                generate_ai_image,
                # open_file_command,
                generate_and_type_code
                
            ],
        }

        # Determine variant from environment
        variant = os.getenv("MARK_VARIANT", "ultra").lower()
        if variant not in FEATURE_MAP:
            print(f"[WARN] Unknown variant '{variant}', defaulting to ultra.")
            variant = "ultra"

        # Initialize only allowed tools
        allowed_tools = FEATURE_MAP[variant]
        self._tools = self._initialize_tools(allowed_tools)

        print(f"[INFO] Assistant initialized with variant: {variant} ({len(allowed_tools)} tools)")

        # Initialize agent with optimized configuration
        super().__init__(
            instructions=self._build_instructions(),
            llm=google.beta.realtime.RealtimeModel(
                voice="Charon",
                temperature=0.8,
                top_p=0.9,
            ),
            tools=self._tools,
        )
        
        # State tracking
        self._last_tool_used: Optional[str] = None
        self._last_tool_success: bool = False
        self._chat_log_path = "chat_log.txt"

    def _initialize_tools(self, tools: List) -> List:
        """Validate and initialize tools with minimal overhead."""
        validated_tools = []
        for tool in tools:
            try:
                if not callable(tool):
                    raise ValueError(f"Tool {getattr(tool, '__name__', str(tool))} is not callable")
                
                # Add minimal metadata
                tool.metadata = {
                    'description': tool.__doc__.strip() if tool.__doc__ else f"Tool: {tool.__name__}",
                    'last_used': None,
                    'usage_count': 0
                }
                validated_tools.append(tool)
            except Exception as e:
                print(f"⚠️ Failed to initialize tool {getattr(tool, '__name__', str(tool))}: {str(e)}")
        
        return validated_tools

    def _build_instructions(self) -> str:
        """Construct optimized instruction set."""
        tool_descriptions = []
        for tool in self._tools:
            tool_name = tool.__name__
            tool_doc = tool.__doc__ if tool.__doc__ else "No description available"
            tool_descriptions.append(f"- {tool_name}: {tool_doc.strip()}")
        
        available_tools = "\n".join(tool_descriptions)
        
        return "\n".join([
            AGENT_INSTRUCTION,
            SESSION_INSTRUCTION,
            AGENT_INSTRUCTION_FOR_TOOLS,
            "You are a multilingual assistant capable of understanding and responding in multiple languages.",
            f"\nAvailable tools:\n{available_tools}",
            "\nWhen a user request requires tool usage, actively use the appropriate tool and provide feedback about the action taken."
        ])

    async def on_tool_call_start(self, tool_call):
        """Handle tool call start event."""
        print(f"🔧 Starting tool call: {tool_call.function_info.name}")
        self._last_tool_used = tool_call.function_info.name
        return await super().on_tool_call_start(tool_call)

    async def on_tool_call_end(self, tool_call, result):
        """Handle tool call completion."""
        success = result and not isinstance(result, Exception)
        self._last_tool_success = success
        
        print(f"🔧 Tool call completed: {tool_call.function_info.name} - {'✅ Success' if success else '❌ Failed'}")
        return await super().on_tool_call_end(tool_call, result)

    async def on_user_turn_completed(self, turn_ctx, new_message):
        """Handle post-processing after user turn completion."""
        user_message = turn_ctx.user_message.text_content if turn_ctx.user_message else "[no user input]"
        assistant_message = new_message.text_content if new_message else "[no assistant reply]"

        # Log conversation
        print(f"\n🗣️ USER: {user_message}")
        print(f"🤖 ASSISTANT: {assistant_message}")
        await self._log_conversation("User", user_message)
        await self._log_conversation("Assistant", assistant_message)

        # Update tool usage tracking
        if self._last_tool_used:
            for tool in self._tools:
                if tool.__name__ == self._last_tool_used:
                    tool.metadata['last_used'] = datetime.now()
                    tool.metadata['usage_count'] += 1
                    break

        return await super().on_user_turn_completed(turn_ctx, new_message)

    async def _log_conversation(self, sender: str, message: str) -> None:
        """Log conversation to file."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            with open(self._chat_log_path, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {sender}: {message}\n")
        except IOError as e:
            print(f"⚠️ Failed to log conversation: {str(e)}")

    async def _check_reminders(self) -> None:
        """Check and announce any reminders."""
        try:
            reminder_text = await get_today_reminder_message_from_db()
            if reminder_text:
                await say_reminder(reminder_text)
        except Exception as e:
            print(f"⚠️ Failed to check reminders: {str(e)}")

async def entrypoint(ctx: agents.JobContext):
    """Optimized main entry point for the agent."""
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(1, max_retries + 1):
        try:
            # Create agent and session
            agent = Assistant()
            session = AgentSession()
            
            # Start session with timeout
            await asyncio.wait_for(
                session.start(
                    room=ctx.room,
                    agent=agent,
                    room_input_options=RoomInputOptions(
                        video_enabled=False,  # Disabled for optimization
                        noise_cancellation=noise_cancellation.BVC(),
                    ),
                ),
                timeout=20.0
            )
            
            # Connect to room
            await ctx.connect()
            
            # Generate startup message
            if os.getenv("MARK_VARIANT", "core").lower() == "ultra" or os.getenv("MARK_VARIANT", "core").lower() == "pro":
                await session.generate_reply(instructions=SESSION_INSTRUCTION)
            else:       
                await session.generate_reply(instructions=SESSION_INSTRUCTION)
            
            # Check for reminders
            await agent._check_reminders()
            
            print("✅ Agent session started successfully")
            break
            
        except Exception as e:
            print(f"❌ Entrypoint failed on attempt {attempt}: {e}")
            if attempt < max_retries:
                await asyncio.sleep(retry_delay)
            else:
                raise

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))