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
    SESSION_INSTRUCTION_2,
    save_user_message,
    save_assistant_message,
    get_today_reminder_message_from_db,
    check_variant_access,
    get_variant_restriction_message
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
        self.variant = os.getenv("MARK_VARIANT", "core").lower()
        if self.variant not in FEATURE_MAP:
            print(f"[WARN] Unknown variant '{self.variant}', defaulting to core.")
            self.variant = "core"

        # Store all available tools for reference
        self.all_tools = {
            "core": FEATURE_MAP["core"],
            "pro": FEATURE_MAP["pro"], 
            "ultra": FEATURE_MAP["ultra"]
        }

        # Initialize only allowed tools
        allowed_tools = FEATURE_MAP[self.variant]
        self._tools = self._initialize_tools(allowed_tools)

        print(f"[INFO] Assistant initialized with variant: {self.variant} ({len(allowed_tools)} tools)")

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

    async def on_before_llm_inference(self, chat_ctx, participant):
        """Intercept user message before it goes to LLM to check for variant restrictions."""
        # Get the latest user message
        if chat_ctx.messages:
            latest_message = chat_ctx.messages[-1]
            if hasattr(latest_message, 'content') and latest_message.content:
                user_text = str(latest_message.content)
                
                # Check for restricted features
                restriction_message = self.check_feature_request(user_text)
                if restriction_message:
                    print(f"🚫 BLOCKING RESTRICTED FEATURE REQUEST: {user_text}")
                    
                    # Add the restriction message as the assistant's response
                    from livekit.agents.llm import ChatMessage
                    restriction_msg = ChatMessage.create(
                        text=restriction_message,
                        role="assistant"
                    )
                    chat_ctx.messages.append(restriction_msg)
                    
                    # Return early to skip LLM processing
                    return chat_ctx
        
        return await super().on_before_llm_inference(chat_ctx, participant)

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

    def check_feature_request(self, message: str) -> Optional[str]:
        """Check if user is requesting unavailable features and return restriction message."""
        message_lower = message.lower()
        
        # Define feature keywords and their required variants
        restricted_features = {
            "ultra": {
                "keywords": [
                    "generate code", "code generation", "write code", "create code",
                    "virus scan", "antivirus", "malware scan", "security scan",
                    "ai image", "generate image", "create image", "dall-e",
                    "excel analysis", "data analysis", "analyze data", "spreadsheet",
                    "visual analysis", "camera", "image processing", "computer vision",
                    "smart clipboard", "advanced automation", "multi task"
                ],
                "features": [
                    "Code Generation", "Virus Scanning", "AI Image Generation", 
                    "Excel Data Analysis", "Visual Analysis", "Advanced Automation"
                ]
            },
            "pro": {
                "keywords": [
                    "send whatsapp", "whatsapp message", "email send",
                    "system info", "system diagnostics", "power action",
                    "shutdown", "restart", "lock system", "notepad write"
                ],
                "features": [
                    "WhatsApp Messaging", "Email Sending", "System Diagnostics",
                    "Power Control", "Document Writing"
                ]
            }
        }
        
        # Check if user is requesting restricted features
        for required_variant, data in restricted_features.items():
            if not check_variant_access(required_variant):  # User doesn't have access
                for keyword in data["keywords"]:
                    if keyword in message_lower:
                        # Find which specific feature was requested
                        if "code" in keyword:
                            feature_name = "Code Generation"
                        elif "virus" in keyword or "scan" in keyword:
                            feature_name = "Virus Scanning"
                        elif "image" in keyword:
                            feature_name = "AI Image Generation"
                        elif "excel" in keyword or "data" in keyword:
                            feature_name = "Data Analysis"
                        elif "camera" in keyword or "visual" in keyword:
                            feature_name = "Visual Analysis"
                        elif "whatsapp" in keyword:
                            feature_name = "WhatsApp Messaging"
                        else:
                            feature_name = keyword.title()
                        
                        return get_variant_restriction_message(feature_name, required_variant.title())
        
        return None

    async def on_user_turn_completed(self, turn_ctx, new_message):
        """Handle post-processing after user turn completion."""
        user_message = turn_ctx.user_message.text_content if turn_ctx.user_message else "[no user input]"
        assistant_message = new_message.text_content if new_message else "[no assistant reply]"

        # Check for restricted feature requests and override response if needed
        if user_message and user_message != "[no user input]":
            restriction_message = self.check_feature_request(user_message)
            if restriction_message:
                # Override the assistant's response with variant restriction message
                print(f"\n🚫 VARIANT RESTRICTION TRIGGERED for: {user_message}")
                print(f"🤖 RESTRICTION MESSAGE: {restriction_message}")
                
                # If we can modify the response, do it
                if hasattr(new_message, 'text_content'):
                    try:
                        new_message.text_content = restriction_message
                        assistant_message = restriction_message
                    except:
                        # If we can't modify the message, at least log it
                        print(f"⚠️ Could not override response, but restriction applies: {restriction_message}")

        # Log conversation
        print(f"\n🗣️ USER: {user_message}")
        print(f"🤖 ASSISTANT: {assistant_message}")
        
        # Save to memory.json for persistent chat history
        if user_message and user_message != "[no user input]":
            save_user_message(user_message)
        if assistant_message and assistant_message != "[no assistant reply]":
            save_assistant_message(assistant_message)
        
        # Also log to text file (existing functionality)
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