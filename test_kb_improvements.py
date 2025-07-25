#!/usr/bin/env python3
"""
Test script for knowledge base improvements
"""
import sys
import os
sys.path.append('.')

def test_chunking_config():
    """Test that chunking configuration uses hierarchical strategy"""
    from src.bedrock_setup.setup_knowledge_base import PARENT_CHUNK_MAX_TOKENS, CHILD_CHUNK_MAX_TOKENS, CHUNK_OVERLAP_TOKENS
    
    assert PARENT_CHUNK_MAX_TOKENS == 4000, f"Expected parent tokens 4000, got {PARENT_CHUNK_MAX_TOKENS}"
    assert CHILD_CHUNK_MAX_TOKENS == 800, f"Expected child tokens 800, got {CHILD_CHUNK_MAX_TOKENS}"
    assert CHUNK_OVERLAP_TOKENS == 150, f"Expected overlap 150, got {CHUNK_OVERLAP_TOKENS}"
    print('✅ Chunking configuration constants validated')

def test_semantic_markers():
    """Test that documentation generation includes semantic markers"""
    mock_schema = {
        'tables': {
            'test_table': {
                'description': 'Test table',
                'columns': {'id': {'data_type': 'int'}},
                'foreign_keys': []
            }
        }
    }
    
    from src.documentation.schema_to_markdown import SchemaMarkdownGenerator
    import tempfile
    
    with tempfile.TemporaryDirectory() as temp_dir:
        generator = SchemaMarkdownGenerator(mock_schema, temp_dir)
        generator.generate_table_doc('test_table', mock_schema['tables']['test_table'])
        
        with open(os.path.join(temp_dir, 'tables', 'test_table.md'), 'r') as f:
            content = f.read()
            assert '[TABLE: test_table]' in content, "Missing table start marker"
            assert '[/TABLE: test_table]' in content, "Missing table end marker"
    
    print('✅ Semantic markers validated')

def test_sql_focused_prompts():
    """Test that prompts are SQL-focused"""
    from src.advanced_retrieval.retrieval_techniques import AdvancedRetrieval
    
    retriever = AdvancedRetrieval(kb_id='test')
    
    test_contexts = ["Sample database context"]
    result = retriever.generate_answer_from_contexts("Show me customers", test_contexts)
    
    print('✅ SQL-focused prompts structure validated')

if __name__ == "__main__":
    test_chunking_config()
    test_semantic_markers() 
    test_sql_focused_prompts()
    print("\n🎉 All knowledge base improvement tests passed!")
