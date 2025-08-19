#!/usr/bin/env python3
"""
Document Upload Script for Guka AI Agent
Uploads all PDF documents from the documents folder to the vector database.
"""

import os
import requests
import json
from pathlib import Path
import time
from typing import List, Dict, Any

# Configuration
AGENT_URL = "http://localhost:8002"
DOCUMENTS_FOLDER = "documents"
SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.txt']

class DocumentUploader:
    def __init__(self, base_url: str = AGENT_URL):
        self.base_url = base_url
        self.session = requests.Session()
        
    def check_agent_health(self) -> bool:
        """Check if the agent is running and healthy."""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Agent Status: {health_data.get('status', 'unknown')}")
                print(f"📊 Dependencies: {health_data.get('dependencies', {})}")
                return True
            else:
                print(f"❌ Agent health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to agent: {e}")
            return False
    
    def get_existing_documents(self, user_id: str = "global_admin") -> List[Dict[str, Any]]:
        """Get list of already uploaded documents."""
        try:
            response = self.session.get(f"{self.base_url}/documents/list?user_id={user_id}")
            if response.status_code == 200:
                return response.json().get('documents', [])
            else:
                print(f"⚠️ Could not fetch existing documents: {response.status_code}")
                return []
        except Exception as e:
            print(f"⚠️ Error fetching existing documents: {e}")
            return []
    
    def upload_document(self, file_path: Path, description: str = None, tags: str = "coffee,farming,kenya", user_id: str = "global_admin") -> bool:
        """Upload a single document to the vector database."""
        try:
            # Prepare the file and form data
            with open(file_path, 'rb') as file:
                files = {'file': (file_path.name, file, 'application/octet-stream')}
                data = {
                    'user_id': user_id,  # Add user_id field
                    'description': description or f"Coffee farming guide: {file_path.name}",
                    'tags': tags
                }
                
                print(f"📤 Uploading: {file_path.name}...")
                response = self.session.post(
                    f"{self.base_url}/documents/upload",
                    files=files,
                    data=data,
                    timeout=60  # Allow time for processing
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Successfully uploaded: {file_path.name}")
                    print(f"   📄 Document ID: {result.get('document_id', 'N/A')}")
                    print(f"   🧩 Chunks created: {result.get('chunks_created', 'N/A')}")
                    return True
                else:
                    print(f"❌ Failed to upload {file_path.name}: {response.status_code}")
                    try:
                        error_detail = response.json()
                        print(f"   Error: {error_detail}")
                    except:
                        print(f"   Error: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error uploading {file_path.name}: {e}")
            return False
    
    def find_documents(self, folder_path: str) -> List[Path]:
        """Find all supported documents in the specified folder."""
        documents = []
        folder = Path(folder_path)
        
        if not folder.exists():
            print(f"❌ Documents folder not found: {folder_path}")
            return documents
        
        for ext in SUPPORTED_EXTENSIONS:
            documents.extend(folder.glob(f"*{ext}"))
            documents.extend(folder.glob(f"*{ext.upper()}"))
        
        return sorted(documents)
    
    def upload_all_documents(self, folder_path: str, user_id: str = "global_admin") -> Dict[str, int]:
        """Upload all documents from the specified folder."""
        documents = self.find_documents(folder_path)
        
        if not documents:
            print(f"📁 No documents found in {folder_path}")
            return {"uploaded": 0, "failed": 0, "skipped": 0}
        
        print(f"📚 Found {len(documents)} documents to upload as global documents:")
        for doc in documents:
            print(f"   📄 {doc.name}")
        print()
        
        # Get existing documents to avoid duplicates
        existing_docs = self.get_existing_documents(user_id)
        existing_names = [doc.get('filename', '') for doc in existing_docs]
        
        uploaded = 0
        failed = 0
        skipped = 0
        
        for doc_path in documents:
            if doc_path.name in existing_names:
                print(f"⏭️ Skipping {doc_path.name} (already uploaded)")
                skipped += 1
                continue
            
            if self.upload_document(doc_path, user_id=user_id):
                uploaded += 1
            else:
                failed += 1
            
            # Small delay to avoid overwhelming the server
            time.sleep(1)
            print()
        
        return {"uploaded": uploaded, "failed": failed, "skipped": skipped}
    
    def test_document_search(self, query: str = "coffee farming kenya") -> bool:
        """Test if uploaded documents are searchable."""
        try:
            print(f"🔍 Testing document search with query: '{query}'")
            response = self.session.post(
                f"{self.base_url}/documents/search",
                json={"query": query, "limit": 3},
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json()
                documents = results.get('documents', [])
                print(f"✅ Search successful! Found {len(documents)} relevant documents:")
                for i, doc in enumerate(documents, 1):
                    print(f"   {i}. {doc.get('filename', 'Unknown')} (similarity: {doc.get('similarity', 0):.3f})")
                return len(documents) > 0
            else:
                print(f"❌ Search failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Search error: {e}")
            return False


def main():
    """Main function to upload documents."""
    print("🌱 Guka AI Agent - Document Upload Tool")
    print("=" * 50)
    
    uploader = DocumentUploader()
    
    # Check agent health
    if not uploader.check_agent_health():
        print("❌ Agent is not available. Please ensure the Guka AI Agent is running.")
        return
    
    print()
    
    # Upload documents
    results = uploader.upload_all_documents(DOCUMENTS_FOLDER)
    
    # Summary
    print("📊 Upload Summary:")
    print(f"   ✅ Uploaded: {results['uploaded']}")
    print(f"   ❌ Failed: {results['failed']}")
    print(f"   ⏭️ Skipped: {results['skipped']}")
    print()
    
    # Test search functionality
    if results['uploaded'] > 0:
        uploader.test_document_search()
    
    print("🎉 Document upload process completed!")


if __name__ == "__main__":
    main()
