# Version Compatibility Notes

## LangChain/LangGraph Version Update

Updated `graph-data-api` to use the same LangChain and LangGraph versions as `chunk-api` for consistency across the project.

### Version Changes

#### Before
```
langgraph==0.0.32
langchain==0.1.0
langchain-core==0.1.10
```

#### After
```
langgraph==1.0.2
langchain==1.0.3
langchain-core==1.0.3
```

### Code Changes Required

#### Import Statement Update

**Before (LangGraph 0.0.x):**
```python
from langgraph.graph import StateGraph, END
```

**After (LangGraph 1.0.x):**
```python
from langgraph.graph import StateGraph
from langgraph.constants import END
```

### Breaking Changes in LangGraph 1.0+

1. **END constant location**: Moved from `langgraph.graph` to `langgraph.constants`
2. **API stability**: 1.0+ versions have stable APIs with better backwards compatibility
3. **Performance improvements**: Better execution performance and memory usage

### Files Modified

1. **requirements.txt**
   - Updated LangGraph: `0.0.32` → `1.0.2`
   - Updated LangChain: `0.1.0` → `1.0.3`
   - Updated LangChain-Core: `0.1.10` → `1.0.3`

2. **graph_workflow.py**
   - Changed import from `langgraph.graph import END` to `langgraph.constants import END`

### Compatibility

These versions are now consistent with:
- `src/chunk-api` (uses langgraph==1.0.2, langchain==1.0.3)
- All other Python services in the project

### Testing Recommendations

After updating dependencies, test the following:

1. **Basic workflow execution**
   ```bash
   # Install updated dependencies
   cd src/graph-data-api
   pip install -r requirements.txt
   
   # Run the API
   python main.py
   ```

2. **Graph building**
   - Test with request documents (doc_type="request")
   - Test with response documents (doc_type="response")
   - Verify Neo4j nodes are created correctly

3. **Error handling**
   - Test with missing doc_type
   - Test with invalid document_id
   - Verify error messages are clear

### Migration Guide for Other Services

If you need to update other services to LangGraph 1.0+, follow these steps:

1. Update `requirements.txt`:
   ```
   langgraph==1.0.2
   langchain==1.0.3
   langchain-core==1.0.3
   ```

2. Update imports in all files using LangGraph:
   ```python
   # Old
   from langgraph.graph import StateGraph, END
   
   # New
   from langgraph.graph import StateGraph
   from langgraph.constants import END
   ```

3. No other code changes should be necessary - the StateGraph API remains the same

### References

- [LangGraph 1.0 Release Notes](https://github.com/langchain-ai/langgraph/releases)
- [LangChain 1.0 Migration Guide](https://python.langchain.com/docs/versions/v0_2/migrating)
