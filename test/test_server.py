#!/usr/bin/env python3
"""
Test script for MCP Bedrock Knowledge Base Server
"""

import asyncio
import json
import subprocess
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_server():
    """Test the MCP server functionality"""
    
    # Server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["../src/mcp_bedrock_kb/server.py"],
        env=None
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                
                # List available tools
                print("🔍 Listing available tools...")
                tools = await session.list_tools()
                print(f"Available tools: {[tool.name for tool in tools.tools]}")
                
                # Test the query_knowledge_base tool
                print("\n🧪 Testing query_knowledge_base tool...")
                result = await session.call_tool(
                    "query_knowledge_base",
                    {"query": "What is AWS Strands?"}
                )
                
                print("✅ Tool call successful!")
                print(f"Response: {result.content[0].text[:200]}...")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_mcp_server())
    sys.exit(0 if success else 1)
