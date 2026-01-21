from python.helpers.tool import Tool, Response
import httpx
import os
import logging

logger = logging.getLogger(__name__)


class KnowledgeSearchTool(Tool):
    """
    Search the clinic's knowledge base for procedures, prices, and information.
    
    Uses Supabase vector search (embeddings) to find relevant information
    about aesthetic procedures, prices, and clinic policies.
    """

    async def execute(self, **kwargs):
        query = self.args.get("query", "")
        
        if not query:
            return Response(
                message="Erro: Consulta vazia. Especifique o que deseja buscar.",
                break_loop=False
            )
        
        # Get Supabase credentials
        supabase_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        openai_key = os.environ.get("OPENAI_API_KEY", "")
        
        if not all([supabase_url, supabase_key]):
            return Response(
                message="Erro: Supabase não configurado.",
                break_loop=False
            )
        
        try:
            # Step 1: Create embedding for the query
            embedding = await self._create_embedding(query, openai_key)
            
            if not embedding:
                # Fallback: simple text search
                return await self._simple_search(query, supabase_url, supabase_key)
            
            # Step 2: Vector search in Supabase
            async with httpx.AsyncClient(timeout=30) as client:
                # Call match_documents RPC function
                resp = await client.post(
                    f"{supabase_url}/rest/v1/rpc/match_documents",
                    headers={
                        "apikey": supabase_key,
                        "Authorization": f"Bearer {supabase_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "query_embedding": embedding,
                        "match_threshold": 0.5,
                        "match_count": 5,
                    }
                )
                
                if resp.status_code != 200:
                    logger.warning(f"Vector search failed: {resp.status_code}")
                    return await self._simple_search(query, supabase_url, supabase_key)
                
                docs = resp.json()
            
            if not docs:
                return Response(
                    message=f"Não encontrei informações sobre '{query}' na base de conhecimento.",
                    break_loop=False
                )
            
            # Format results
            results = []
            for doc in docs[:3]:  # Top 3 results
                title = doc.get("title", "Sem título")
                content = doc.get("content", "")[:500]  # Limit content
                results.append(f"**{title}**\n{content}")
            
            response_text = f"Informações encontradas sobre '{query}':\n\n" + "\n\n---\n\n".join(results)
            
            return Response(
                message=response_text,
                break_loop=False
            )
            
        except Exception as e:
            logger.error(f"Knowledge search error: {str(e)}")
            return Response(
                message=f"Erro ao buscar informações: {str(e)}",
                break_loop=False
            )
    
    async def _create_embedding(self, text: str, api_key: str) -> list | None:
        """Create embedding using OpenAI API."""
        if not api_key:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "input": text,
                        "model": "text-embedding-3-small",
                    }
                )
                resp.raise_for_status()
                data = resp.json()
                return data["data"][0]["embedding"]
        except Exception as e:
            logger.warning(f"Embedding creation failed: {str(e)}")
            return None
    
    async def _simple_search(self, query: str, supabase_url: str, supabase_key: str) -> Response:
        """Fallback: simple text search in knowledge base."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Search in documents table with text matching
                resp = await client.get(
                    f"{supabase_url}/rest/v1/knowledge_base",
                    headers={
                        "apikey": supabase_key,
                        "Authorization": f"Bearer {supabase_key}",
                    },
                    params={
                        "or": f"(title.ilike.*{query}*,content.ilike.*{query}*)",
                        "limit": 5,
                    }
                )
                
                if resp.status_code != 200:
                    return Response(
                        message=f"Não consegui pesquisar a base de conhecimento.",
                        break_loop=False
                    )
                
                docs = resp.json()
                
                if not docs:
                    return Response(
                        message=f"Não encontrei informações sobre '{query}'.",
                        break_loop=False
                    )
                
                results = []
                for doc in docs[:3]:
                    title = doc.get("title", "Sem título")
                    content = doc.get("content", "")[:300]
                    results.append(f"**{title}**\n{content}")
                
                return Response(
                    message=f"Informações sobre '{query}':\n\n" + "\n\n".join(results),
                    break_loop=False
                )
                
        except Exception as e:
            return Response(
                message=f"Erro na busca: {str(e)}",
                break_loop=False
            )

    async def before_execution(self, **kwargs):
        query = self.args.get("query", "")[:30]
        self.log = self.agent.context.log.log(
            type="tool",
            heading=f"🔍 Buscando: {query}...",
            content=""
        )

    async def after_execution(self, response, **kwargs):
        if self.log:
            self.log.update(finished=True)
