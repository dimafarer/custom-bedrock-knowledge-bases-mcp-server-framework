# MCP Bedrock Knowledge Base Server - Complete Code Explanation

This document explains every line of our MCP Bedrock Knowledge Base server code for new programmers. We'll cover the "why" behind each decision and how the MCP protocol works from beginning to end.

## File: `src/mcp_bedrock_kb/server.py`

### The Shebang and Module Documentation

```python
#!/usr/bin/env python3
```
**What**: This is called a "shebang" - it tells the operating system which interpreter to use when running this file directly.
**Why**: Allows us to run `./server.py` instead of `python server.py`. The `env` command finds Python3 wherever it's installed on the system.

```python
"""
MCP Bedrock Knowledge Base Server

A minimal MCP server that connects to AWS Bedrock Knowledge Base
to provide enhanced documentation queries.
"""
```
**What**: A module docstring - Python's way of documenting what an entire file/module does.
**Why**: Good documentation helps other developers (and future you) understand the purpose. Triple quotes allow multi-line strings and are the Python standard for documentation.

### Imports - Bringing in External Libraries

```python
import asyncio
```
**What**: Python's built-in library for asynchronous programming.
**Why**: MCP servers need to handle multiple requests without blocking. `asyncio` lets us write code that can pause and resume, allowing other tasks to run while we wait for AWS responses.

```python
import os
```
**What**: Python's built-in operating system interface library.
**Why**: We need to read environment variables (like AWS credentials and configuration) from the system.

```python
from mcp.server.models import InitializationOptions
```
**What**: Imports a specific class from the MCP library.
**Why**: `InitializationOptions` tells the MCP client what our server can do and how to communicate with it. We import only what we need to keep our code clean.

```python
import mcp.types as types
```
**What**: Imports the MCP types module and gives it a shorter name.
**Why**: MCP has specific data types (like `Tool`, `TextContent`) that define the protocol. The `as types` makes our code more readable: `types.Tool` instead of `mcp.types.Tool`.

```python
from mcp.server import NotificationOptions, Server
```
**What**: Imports the main Server class and notification settings.
**Why**: `Server` is the core of our MCP server - it handles all the protocol communication. `NotificationOptions` configures how our server sends updates to clients.

```python
import boto3
```
**What**: AWS SDK (Software Development Kit) for Python.
**Why**: This is how we communicate with AWS services. We'll use it specifically to connect to AWS Bedrock Knowledge Base.

```python
from botocore.exceptions import ClientError, NoCredentialsError
```
**What**: Imports specific AWS error types.
**Why**: AWS operations can fail in predictable ways (no credentials, access denied, etc.). By importing these specific errors, we can handle them gracefully and give users helpful error messages.

```python
from dotenv import load_dotenv
```
**What**: Imports a library for loading environment variables from `.env` files.
**Why**: Environment variables are the secure way to store configuration like AWS credentials and Knowledge Base IDs. The `dotenv` library lets us use a `.env` file for local development.

### Environment Configuration

```python
# Load environment variables
load_dotenv()
```
**What**: Loads variables from a `.env` file into the environment.
**Why**: This allows developers to create a `.env` file with their specific AWS configuration without hardcoding sensitive information in the code.

```python
# Configuration from environment variables
KNOWLEDGE_BASE_ID = os.getenv("BEDROCK_KB_ID")
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
BEDROCK_MODEL_ARN = os.getenv("BEDROCK_MODEL_ARN")
```
**What**: Reads configuration values from environment variables.
**Why**: This makes our server configurable without changing code. Each deployment can have different Knowledge Base IDs and regions.

**Breaking down each line**:
- `os.getenv("BEDROCK_KB_ID")`: Gets the Knowledge Base ID, returns `None` if not set
- `os.getenv("AWS_REGION", "us-west-2")`: Gets the AWS region, defaults to "us-west-2" if not set
- `os.getenv("BEDROCK_MODEL_ARN")`: Gets the model ARN (Amazon Resource Name) for the AI model to use

```python
# Validate required environment variables
if not KNOWLEDGE_BASE_ID:
    raise ValueError("BEDROCK_KB_ID environment variable is required")
if not BEDROCK_MODEL_ARN:
    raise ValueError("BEDROCK_MODEL_ARN environment variable is required")
```
**What**: Checks that required configuration is present and fails fast if not.
**Why**: Better to fail immediately with a clear error message than to fail later with a confusing AWS error. This helps developers debug configuration issues quickly.

### Creating the Server Instance

```python
# Create server instance
server = Server("bedrock-kb")
```
**What**: Creates a new MCP server with the name "bedrock-kb".
**Why**: This is our server's identity. MCP clients will see this name when they connect. The name should be descriptive and unique among your MCP servers.

### Tool Discovery - What Can Our Server Do?

```python
@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
```
**What**: A decorator that registers this function to handle "list tools" requests from MCP clients.
**Why**: When a client (like Amazon Q CLI) connects to our server, the first thing it does is ask "what tools do you have?" This function answers that question.

**Breaking down the syntax**:
- `@server.list_tools()`: Decorator - tells the server "call this function when someone asks for available tools"
- `async def`: Asynchronous function - can pause and resume without blocking other operations
- `-> list[types.Tool]`: Type hint - tells other developers this returns a list of Tool objects

```python
"""Return available tools"""
```
**What**: Function docstring explaining what this function does.
**Why**: Documents the function's purpose for other developers.

```python
return [
    types.Tool(
        name="query_knowledge_base",
        description="Query AWS Bedrock Knowledge Base for information",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The question or topic to search for in the knowledge base"
                }
            },
            "required": ["query"]
        }
    )
]
```
**What**: Returns a list containing one Tool object that describes our knowledge base query capability.
**Why**: This defines what our tool does and what input it expects. The MCP client uses this information to know how to call our tool.

**Breaking down the Tool definition**:
- `name`: Unique identifier for the tool ("query_knowledge_base")
- `description`: Human-readable explanation of what the tool does
- `inputSchema`: JSON Schema defining the expected input format
  - `"type": "object"`: Input should be a dictionary/object
  - `"properties"`: Defines what fields the object can have
  - `"query"`: The field name for the user's question
  - `"type": "string"`: The query should be text
  - `"required": ["query"]`: The query field must be provided

### Tool Execution - Actually Doing the Work

```python
@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
```
**What**: Decorator that registers this function to handle tool execution requests.
**Why**: When a client wants to actually use a tool, this function gets called. It's the router that decides which tool function to call.

**Parameter explanation**:
- `name: str`: Which tool the client wants to use (should match a tool name from `list_tools`)
- `arguments: dict | None`: The input data from the client (could be None if no arguments provided)
- `-> list[types.TextContent]`: Returns a list of text responses to send back to the client

```python
"""Handle tool calls"""
```
**What**: Function docstring.

```python
if name == "query_knowledge_base":
    query = arguments.get("query", "") if arguments else ""
    return await query_knowledge_base(query)
else:
    raise ValueError(f"Unknown tool: {name}")
```
**What**: Checks which tool was requested and routes to the appropriate handler function.
**Why**: Our server might have multiple tools in the future. We need to route each request to the right handler.

**Breaking down the logic**:
- `if name == "query_knowledge_base"`: Check if this is our knowledge base query tool
- `arguments.get("query", "")`: Safely get the "query" field from arguments, default to empty string if missing
- `if arguments else ""`: Handle the case where arguments is None (no input provided)
- `await query_knowledge_base(query)`: Call our query function and wait for the result
- `raise ValueError(...)`: If an unknown tool is requested, throw an error with a helpful message

### The Core Query Function - Where the Magic Happens

```python
async def query_knowledge_base(query: str) -> list[types.TextContent]:
```
**What**: The main function that queries AWS Bedrock Knowledge Base.
**Why**: Separating this logic into its own function makes our code more organized, testable, and reusable.

```python
"""Query the Bedrock Knowledge Base"""
```
**What**: Function docstring.

#### Input Validation

```python
if not query.strip():
    return [types.TextContent(
        type="text",
        text="Please provide a query to search the knowledge base."
    )]
```
**What**: Validates that the user provided a non-empty query.
**Why**: Better user experience than sending empty queries to AWS (which would cost money and return poor results). The `.strip()` removes whitespace, so "   " would be considered empty.

**Breaking down the response**:
- `types.TextContent`: MCP's standard way to return text to the client
- `type="text"`: Specifies this is plain text content
- `text="..."`: The actual message to display to the user

#### AWS Client Setup and Query Execution

```python
try:
    # Create Bedrock client
    bedrock_client = boto3.client(
        'bedrock-agent-runtime',
        region_name=AWS_REGION
    )
```
**What**: Creates an AWS client for the Bedrock Agent Runtime service.
**Why**: This is how we communicate with AWS Bedrock. The `bedrock-agent-runtime` service specifically handles knowledge base queries (as opposed to direct model calls).

**Breaking it down**:
- `boto3.client()`: Creates an AWS service client
- `'bedrock-agent-runtime'`: The specific AWS service we want to use
- `region_name=AWS_REGION`: Which AWS region to connect to (from our environment variables)

```python
# Query the knowledge base
response = bedrock_client.retrieve_and_generate(
    input={
        'text': query
    },
    retrieveAndGenerateConfiguration={
        'type': 'KNOWLEDGE_BASE',
        'knowledgeBaseConfiguration': {
            'knowledgeBaseId': KNOWLEDGE_BASE_ID,
            'modelArn': BEDROCK_MODEL_ARN
        }
    }
)
```
**What**: Makes the actual API call to AWS Bedrock to query the knowledge base.
**Why**: This is the core functionality - taking the user's question and getting an AI-generated answer based on the knowledge base content.

**Breaking down the API call**:
- `retrieve_and_generate()`: AWS API method that both searches the knowledge base AND generates a response
- `input={'text': query}`: The user's question
- `retrieveAndGenerateConfiguration`: Configuration for how to process the query
  - `'type': 'KNOWLEDGE_BASE'`: We're querying a knowledge base (not just a model)
  - `'knowledgeBaseId'`: Which knowledge base to search (from our environment variables)
  - `'modelArn'`: Which AI model to use for generating the response (from our environment variables)

#### Response Processing

```python
# Extract the generated response
generated_text = response['output']['text']
```
**What**: Extracts the AI-generated answer from the AWS response.
**Why**: The AWS response is a complex dictionary with metadata. We just want the actual answer text.

```python
# Format response with sources if available
formatted_response = f"**Query**: {query}\n\n**Answer**: {generated_text}"
```
**What**: Creates a nicely formatted response that includes both the original question and the answer.
**Why**: This makes it clear to the user what question was answered, especially useful in chat interfaces where the conversation might be long.

**Breaking down the formatting**:
- `f"..."`: F-string for string interpolation (inserting variables into strings)
- `**Query**`: Markdown-style bold formatting
- `\n\n`: Two newlines create a paragraph break

```python
# Add source citations if available
if 'citations' in response and response['citations']:
    formatted_response += "\n\n**Sources**:"
    for i, citation in enumerate(response['citations'], 1):
        if 'retrievedReferences' in citation:
            for ref in citation['retrievedReferences']:
                if 'location' in ref and 's3Location' in ref['location']:
                    source_uri = ref['location']['s3Location'].get('uri', 'Unknown source')
                    formatted_response += f"\n{i}. {source_uri}"
```
**What**: Adds source citations to the response if AWS provides them.
**Why**: Transparency - users can see what documents the AI used to generate the answer. This builds trust and allows users to verify information.

**Breaking down the citation processing**:
- `if 'citations' in response and response['citations']`: Check if citations exist and aren't empty
- `enumerate(response['citations'], 1)`: Loop through citations with numbering starting at 1
- Multiple nested `if` statements: Safely navigate the complex AWS response structure
- `source_uri = ref['location']['s3Location'].get('uri', 'Unknown source')`: Extract the document location, with fallback

```python
return [types.TextContent(
    type="text",
    text=formatted_response
)]
```
**What**: Returns the formatted response to the MCP client.
**Why**: This is how we send the answer back to the user through the MCP protocol.

### Error Handling - When Things Go Wrong

```python
except NoCredentialsError:
    return [types.TextContent(
        type="text",
        text="❌ AWS credentials not found. Please configure AWS CLI with 'aws configure' or set environment variables."
    )]
```
**What**: Handles the case where AWS credentials aren't configured.
**Why**: This is a common setup issue. Providing a clear, actionable error message helps users fix the problem quickly.

```python
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'AccessDeniedException':
        return [types.TextContent(
            type="text",
            text="❌ Access denied. Please ensure your AWS credentials have bedrock:RetrieveAndGenerate permissions."
        )]
    else:
        return [types.TextContent(
            type="text",
            text=f"❌ AWS error ({error_code}): {e.response['Error']['Message']}"
        )]
```
**What**: Handles AWS-specific errors with helpful messages.
**Why**: AWS errors can be cryptic. We translate them into user-friendly messages with specific solutions.

**Breaking down the error handling**:
- `ClientError`: AWS's general error type for API problems
- `error_code = e.response['Error']['Code']`: Extract the specific error type
- `AccessDeniedException`: Common error when permissions are wrong
- Generic fallback for other AWS errors with the actual error message

```python
except Exception as e:
    return [types.TextContent(
        type="text",
        text=f"❌ Unexpected error: {str(e)}"
    )]
```
**What**: Catches any other unexpected errors.
**Why**: Defensive programming - we don't want our server to crash on unexpected errors. This provides a fallback that at least tells the user something went wrong.

### Server Startup - Bringing It All Together

```python
async def main():
    """Main entry point"""
    from mcp.server.stdio import stdio_server
```
**What**: Main function that starts our server. Import is inside the function to avoid event loop issues.
**Why**: Good practice to have a main function rather than running code at module level. The import timing prevents asyncio setup problems.

```python
async with stdio_server() as (read_stream, write_stream):
```
**What**: Creates input/output streams for MCP communication.
**Why**: MCP servers communicate via stdin/stdout (standard input/output). This sets up those communication channels.

**Breaking down the syntax**:
- `async with`: Asynchronous context manager - automatically sets up and cleans up resources
- `stdio_server()`: Creates standard input/output server for MCP communication
- `as (read_stream, write_stream)`: Unpacks the returned streams into two variables

```python
await server.run(
    read_stream,
    write_stream,
    InitializationOptions(
        server_name="bedrock-kb",
        server_version="1.0.0",
        capabilities=server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={},
        ),
    ),
)
```
**What**: Starts the server with configuration options and begins listening for MCP requests.
**Why**: This is where our server actually begins operating - it will now respond to tool requests from MCP clients.

**Breaking down the configuration**:
- `read_stream, write_stream`: How the server communicates with clients
- `server_name`: Identity of our server (matches what we used when creating the server)
- `server_version`: Version number for compatibility tracking
- `capabilities`: What features our server supports (generated automatically)
- `notification_options`: How to handle notifications (empty for now)
- `experimental_capabilities`: Future features (empty for now)

### Script Entry Point

```python
if __name__ == "__main__":
    asyncio.run(main())
```
**What**: Only runs if this file is executed directly (not imported as a module).
**Why**: Allows our file to be both a runnable script and an importable module for testing.

**Breaking it down**:
- `if __name__ == "__main__"`: Python idiom - only true when file is run directly
- `asyncio.run(main())`: Starts the async event loop and runs our main function

## How the MCP Protocol Works - The Complete Flow

### 1. Client Connection
1. MCP client (like Amazon Q CLI) starts our server process
2. Client and server establish stdin/stdout communication
3. Client sends initialization request
4. Server responds with capabilities (what tools we offer)

### 2. Tool Discovery
1. Client asks: "What tools do you have?" (`list_tools` request)
2. Our `handle_list_tools()` function responds with tool definitions
3. Client now knows we have a `query_knowledge_base` tool

### 3. Tool Execution
1. User asks a question in the client
2. Client decides to use our `query_knowledge_base` tool
3. Client sends `call_tool` request with the user's question
4. Our `handle_call_tool()` function routes to `query_knowledge_base()`
5. We query AWS Bedrock and return the formatted response
6. Client displays the response to the user

### 4. Error Handling
- At any step, if something goes wrong, we return helpful error messages
- The MCP protocol ensures errors are communicated clearly to the client

## Key Concepts for New Programmers

1. **Async/Await**: Allows code to pause and resume, enabling multiple operations simultaneously without blocking
2. **Decorators (@)**: Modify or register functions without changing their core code
3. **Type Hints**: Help other developers understand what data types functions expect and return
4. **Context Managers (with)**: Automatically handle setup and cleanup of resources
5. **JSON Schema**: Standard way to describe the structure and requirements of data
6. **Environment Variables**: Secure way to configure applications without hardcoding sensitive information
7. **Error Handling**: Gracefully managing when things go wrong and providing helpful feedback

## Why This Architecture?

- **Separation of Concerns**: Each function has one clear responsibility
- **Error Handling**: Clear, actionable error messages when things go wrong
- **Security**: Sensitive configuration stored in environment variables, not code
- **Extensibility**: Easy to add more tools or modify existing ones
- **Standards Compliance**: Follows MCP protocol exactly for maximum compatibility
- **Testability**: Each piece can be tested independently
- **Maintainability**: Clear structure makes it easy to understand and modify

## Production Considerations

This server is production-ready but could be enhanced with:
- Logging for debugging and monitoring
- Rate limiting to prevent abuse
- Caching to reduce AWS costs
- Input sanitization for security
- Configuration validation
- Health checks
- Metrics collection

The current implementation prioritizes simplicity and clarity while maintaining robustness through comprehensive error handling.
