"use strict";
exports.id = 280;
exports.ids = [280];
exports.modules = {

/***/ 17280:
/***/ ((__unused_webpack_module, exports, __webpack_require__) => {

var __webpack_unused_export__;

/**
 * SubAgentExecutor — encapsulates a sub-agent's full converseStream lifecycle.
 *
 * Each instance runs its own event loop (stream → handle events → execute tools
 * → send results → repeat) until the sub-agent sends endOfConversation.
 *
 * All state is local to this instance — no shared mutable state with the main
 * agent's EventLoopExecutor or other sub-agents. The only shared resources are
 * the FrontendServiceClient (stateless) and the AbortSignal (read-only
 * propagation from parent).
 *
 * Recursive nesting is supported: tool execution uses the shared
 * createToolsQueuedHandler from handoffDispatcher, which can extract and
 * dispatch further handoff tools via new SubAgentExecutor instances.
 */
__webpack_unused_export__ = ({ value: true });
exports.SubAgentExecutor = void 0;
const toolUseEventHandler_1 = __webpack_require__(43414);
const logger_1 = __webpack_require__(98555);
const aws_transform_custom_client_1 = __webpack_require__(24881);
const handoffDispatcher_1 = __webpack_require__(38795);
const input_1 = __webpack_require__(707);
const USER_INPUT_PROMPT = '\x1B[35m> \x1B[0m';
// ---------------------------------------------------------------------------
// SubAgentExecutor
// ---------------------------------------------------------------------------
class SubAgentExecutor {
    fesClient;
    conversationId;
    tools;
    clientMetadata;
    abortSignal;
    loggingManager;
    subToolHandler;
    agentId;
    agentType;
    interactiveMode;
    // Handoff-aware tool execution handler (supports nested sub-agents)
    toolsQueuedHandler;
    dispatchContext;
    executionId;
    // Local state for this sub-agent's conversation
    agentResponse = '';
    endOfConvo = false;
    currentCheckpointId;
    fatalError;
    constructor(options) {
        this.fesClient = options.fesClient;
        this.conversationId = options.conversationId;
        this.tools = options.tools;
        this.clientMetadata = options.clientMetadata;
        this.abortSignal = options.abortSignal;
        this.loggingManager = options.loggingManager;
        this.agentId = options.agentId;
        this.agentType = options.agentType;
        this.interactiveMode = options.interactiveMode;
        this.executionId = options.executionId;
        // Each sub-agent gets its own ToolUseEventHandler instance
        this.subToolHandler = new toolUseEventHandler_1.ToolUseEventHandler({
            loggingManager: options.loggingManager,
            trustAllTools: options.trustAllTools,
            execMode: options.execMode,
            interactiveMode: options.interactiveMode,
            testMode: options.testMode,
            codeRepositoryPath: options.codeRepositoryPath,
            abortSignal: options.abortSignal,
        });
        // Build handoff dispatch context — enables this sub-agent to spawn
        // nested sub-agents via the same mechanism as the main agent.
        // Stored as an instance field so executionId can be updated when
        // the backend returns it via ConversationEvent.
        this.dispatchContext = {
            fesClient: options.fesClient,
            conversationId: options.conversationId,
            tools: options.tools,
            clientMetadata: options.clientMetadata,
            abortSignal: options.abortSignal,
            loggingManager: options.loggingManager,
            trustAllTools: options.trustAllTools,
            execMode: options.execMode,
            interactiveMode: options.interactiveMode,
            testMode: options.testMode,
            codeRepositoryPath: options.codeRepositoryPath,
            executionId: this.executionId,
        };
        this.toolsQueuedHandler = (0, handoffDispatcher_1.createToolsQueuedHandler)(this.dispatchContext);
    }
    /**
     * Execute the sub-agent's converseStream lifecycle to completion.
     *
     * @param toolUseId - The toolUseId of the handoff tool from the parent agent
     * @param handoffInput - The message to send as the initial user message to the sub-agent
     * @returns A ToolResult containing the sub-agent's accumulated response
     */
    async execute(toolUseId, handoffInput) {
        try {
            // Build local event handlers that only mutate this instance's state
            const handlers = this.createEventHandlers();
            // AgentState for initial request (eventType: INITIAL creates the sub-agent session)
            const initialAgentState = {
                agentId: this.agentId,
                agentType: this.agentType,
                eventType: aws_transform_custom_client_1.AgentEventType.INITIAL,
                ...(this.executionId && { executionId: this.executionId }),
            };
            // AgentState for continuation requests (no eventType — implies continuation)
            const continueAgentState = {
                agentId: this.agentId,
                agentType: this.agentType,
            };
            // Build and send the initial converseStream request
            const initialRequest = {
                conversationState: {
                    conversationId: this.conversationId,
                    currentMessage: {
                        timestamp: new Date(),
                        content: handoffInput,
                        source: aws_transform_custom_client_1.Source.USER,
                    },
                },
                clientMetadata: this.clientMetadata,
                agentState: initialAgentState,
                tools: this.tools,
                toolResults: [],
            };
            logger_1.logger.debug(`SubAgent[${toolUseId}]: Starting converseStream`);
            await this.fesClient.converseStream(initialRequest, handlers, this.abortSignal);
            // Event loop: continue until endOfConversation or fatal error
            while (!this.endOfConvo && !this.fatalError) {
                // Check abort
                if (this.abortSignal?.aborted) {
                    logger_1.logger.debug(`SubAgent[${toolUseId}]: Aborted by user`);
                    return {
                        toolUseId,
                        content: 'Sub-agent execution was aborted by user',
                        status: aws_transform_custom_client_1.ToolUseStatus.ERROR,
                    };
                }
                if (this.subToolHandler.hasToolsToExecute()) {
                    // Use the shared handoff-aware tool execution handler.
                    // This extracts handoff tools, executes regular tools sequentially,
                    // dispatches handoff tools in parallel via new SubAgentExecutor instances
                    // (recursive nesting), and returns all results merged.
                    const toolResults = await this.toolsQueuedHandler(this.subToolHandler);
                    const continueRequest = {
                        conversationState: {
                            conversationId: this.conversationId,
                            checkpointId: this.currentCheckpointId,
                            currentMessage: {
                                timestamp: new Date(),
                                content: '',
                                source: aws_transform_custom_client_1.Source.USER,
                            },
                        },
                        clientMetadata: this.clientMetadata,
                        agentState: continueAgentState,
                        tools: this.tools,
                        toolResults,
                    };
                    logger_1.logger.debug(`SubAgent[${toolUseId}]: Sending ${toolResults.length} tool results back`);
                    this.agentResponse = '';
                    await this.fesClient.converseStream(continueRequest, handlers, this.abortSignal);
                }
                else if (!this.endOfConvo && !this.fatalError) {
                    if (!this.interactiveMode) {
                        logger_1.logger.error(`SubAgent[${toolUseId}]: Non-interactive sub-agent reached invalid state`);
                        this.fatalError = new Error('Sub-agent has no tools to execute and is not in interactive mode');
                        break;
                    }
                    // Interactive sub-agent wants user input — prompt user directly
                    logger_1.logger.debug(`SubAgent[${toolUseId}]: Sub-agent awaiting user input`);
                    console.log('\n');
                    const userInput = await input_1.InputManager.getInstance().readInput(USER_INPUT_PROMPT);
                    if (!userInput)
                        continue;
                    const continueRequest = {
                        conversationState: {
                            conversationId: this.conversationId,
                            checkpointId: this.currentCheckpointId,
                            currentMessage: {
                                timestamp: new Date(),
                                content: userInput,
                                source: aws_transform_custom_client_1.Source.USER,
                            },
                        },
                        clientMetadata: this.clientMetadata,
                        agentState: continueAgentState,
                        tools: this.tools,
                        toolResults: [],
                    };
                    this.agentResponse = '';
                    await this.fesClient.converseStream(continueRequest, handlers, this.abortSignal);
                }
            }
            // Check for fatal error
            if (this.fatalError) {
                logger_1.logger.error(`SubAgent[${toolUseId}]: Fatal error: ${this.fatalError.message}`);
                return {
                    toolUseId,
                    content: `Sub-agent execution failed: ${this.fatalError.message}`,
                    status: aws_transform_custom_client_1.ToolUseStatus.ERROR,
                };
            }
            logger_1.logger.debug(`SubAgent[${toolUseId}]: Completed successfully, response length: ${this.agentResponse.length}`);
            return {
                toolUseId,
                content: this.agentResponse || 'Sub-agent completed with no response',
                status: aws_transform_custom_client_1.ToolUseStatus.SUCCESS,
            };
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            logger_1.logger.error(`SubAgent[${toolUseId}]: Unhandled error: ${errorMessage}`);
            return {
                toolUseId,
                content: `Sub-agent execution failed: ${errorMessage}`,
                status: aws_transform_custom_client_1.ToolUseStatus.ERROR,
            };
        }
    }
    /**
     * Create event handlers that are local to this sub-agent instance.
     * These closures only mutate state on this SubAgentExecutor, not the main agent.
     */
    createEventHandlers() {
        const startOfConversationHandler = (_event) => {
            logger_1.logger.debug(`SubAgent: Received startOfConversation`);
        };
        const agentResponseHandler = (event) => {
            logger_1.logger.debug(`SubAgent: Received agent response`);
            this.agentResponse += event.content;
            this.loggingManager.handleAgentResponse(event);
        };
        const toolUseHandler = (event) => {
            logger_1.logger.debug(`SubAgent: Received tool use event`);
            this.subToolHandler.handleToolUseEvent(event);
        };
        const conversationEventHandler = (event) => {
            logger_1.logger.debug(`SubAgent: Received conversation event`);
            if (event.checkpointId) {
                this.currentCheckpointId = event.checkpointId;
            }
            if (event.executionId) {
                this.executionId = event.executionId;
                // Propagate to dispatch context so nested sub-agents inherit the executionId
                this.dispatchContext.executionId = event.executionId;
                logger_1.logger.debug(`Received executionId in SubAgentExecutor conversationEventHandler: ${event.executionId}`);
            }
            if (event.endOfConversation) {
                this.endOfConvo = true;
            }
        };
        const endOfConversationHandler = (_event) => {
            logger_1.logger.debug(`SubAgent: Received end of conversation`);
            this.endOfConvo = true;
        };
        const errorHandler = async (error) => {
            // If aborted, don't treat as fatal
            if (this.abortSignal?.aborted) {
                logger_1.logger.debug('SubAgent: Error occurred due to user abort, ignoring');
                return;
            }
            const errorMessage = error instanceof Error ? error.message : JSON.stringify(error);
            logger_1.logger.error(`SubAgent: Stream error: ${errorMessage}`);
            this.fatalError = error instanceof Error ? error : new Error(errorMessage);
        };
        return {
            startOfConversationHandler,
            agentResponseHandler,
            toolUseHandler,
            conversationEventHandler,
            endOfConversationHandler,
            errorHandler,
        };
    }
}
exports.SubAgentExecutor = SubAgentExecutor;
//# sourceMappingURL=subAgentExecutor.js.map

/***/ })

};
;