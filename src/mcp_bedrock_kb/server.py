#!/usr/bin/env python3
"""
MCP Bedrock Knowledge Base Server

A minimal MCP server that connects to AWS Bedrock Knowledge Base
to provide enhanced documentation queries.
"""

import asyncio
import os
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration from environment variables
KNOWLEDGE_BASE_ID = os.getenv("BEDROCK_KB_ID")
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
BEDROCK_MODEL_ARN = os.getenv("BEDROCK_MODEL_ARN")

# Validate required environment variables
if not KNOWLEDGE_BASE_ID:
    raise ValueError("BEDROCK_KB_ID environment variable is required")
if not BEDROCK_MODEL_ARN:
    raise ValueError("BEDROCK_MODEL_ARN environment variable is required")

# Create server instance
server = Server("bedrock-kb")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """Return available tools"""
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

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    """Handle tool calls"""
    if name == "query_knowledge_base":
        query = arguments.get("query", "") if arguments else ""
        return await query_knowledge_base(query)
    else:
        raise ValueError(f"Unknown tool: {name}")

async def query_knowledge_base(query: str) -> list[types.TextContent]:
    """Query the Bedrock Knowledge Base"""
    if not query.strip():
        return [types.TextContent(
            type="text",
            text="Please provide a query to search the knowledge base."
        )]
    
    try:
        # Create Bedrock client
        bedrock_client = boto3.client(
            'bedrock-agent-runtime',
            region_name=AWS_REGION
        )
        
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
        
        # Extract the generated response
        generated_text = response['output']['text']
        
        # Format response with sources if available
        formatted_response = f"**Query**: {query}\n\n**Answer**: {generated_text}"
        
        # Add source citations if available
        if 'citations' in response and response['citations']:
            formatted_response += "\n\n**Sources**:"
            for i, citation in enumerate(response['citations'], 1):
                if 'retrievedReferences' in citation:
                    for ref in citation['retrievedReferences']:
                        if 'location' in ref and 's3Location' in ref['location']:
                            source_uri = ref['location']['s3Location'].get('uri', 'Unknown source')
                            formatted_response += f"\n{i}. {source_uri}"
        
        return [types.TextContent(
            type="text",
            text=formatted_response
        )]
        
    except NoCredentialsError:
        return [types.TextContent(
            type="text",
            text="❌ AWS credentials not found. Please configure AWS CLI with 'aws configure' or set environment variables."
        )]
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
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"❌ Unexpected error: {str(e)}"
        )]

async def main():
    """Main entry point"""
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
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

if __name__ == "__main__":
    asyncio.run(main())
