# Performance Optimization Analysis for github2file

## Current Performance Bottlenecks

### 1. Major Issue: `os.walk()` Traverses Excluded Directories
**Location:** `g2f.py:225`
- `os.walk()` walks the entire directory tree including excluded directories like `.venv`, `node_modules`, etc.
- Directory exclusion is only checked per-file after walking (lines 246-248)
- This causes long execution times when encountering deep nested folders

### 2. Redundant File Filtering
**Location:** `g2f.py:233-248`
- Multiple filter functions called for each file
- Could be optimized with early exits and combined checks

### 3. Deep Nested Folder Traversal
- No depth limiting mechanism
- Can get stuck in symlink loops or very deep hierarchies
- No protection against infinite directory structures

## Low-Hanging Fruit Optimizations

### 1. Skip Excluded Directories During `os.walk()`
**Impact:** High - eliminates traversing large excluded directories entirely

```python
for root, dirs, files in os.walk(start_path):
    # Modify dirs in-place to skip excluded directories
    dirs[:] = [d for d in dirs if d not in excluded_dirs]
    # Continue with file processing...
```

### 2. Early Directory Filtering
**Impact:** High - skip entire directory branches early

```python
# Check if current root should be excluded before processing files
if any(excluded_dir in root for excluded_dir in excluded_dirs):
    continue
```

### 3. Add Maximum Depth Limit
**Impact:** Medium - prevents infinite depth traversal

```python
depth = root.replace(start_path, '').count(os.sep)
if depth > max_depth:
    dirs.clear()  # Don't traverse deeper
    continue
```

## Performance Optimization Hypotheses

### Fast Wins (Low effort, high impact)
1. **Directory pruning during `os.walk()`**
   - Modify `dirs` list to skip excluded directories
   - Single biggest performance gain possible

2. **Root-level exclusion check**
   - Skip entire directory branches before file processing
   - Eliminates redundant file checks

3. **Depth limiting**
   - Add `--max-depth` command line option
   - Prevents runaway traversal

### Medium Effort Optimizations
1. **Parallel directory processing**
   - Use `multiprocessing` to process directories in parallel
   - Beneficial for codebases with many independent directories

2. **File filtering optimization**
   - Combine multiple filter checks into single optimized function
   - Reduce function call overhead

3. **Lazy file content reading**
   - Only read file contents when all filters pass
   - Avoid I/O for files that will be excluded

### Advanced Optimizations
1. **`pathlib` migration**
   - More efficient path operations than `os.path`
   - Better cross-platform compatibility

2. **Directory scanning cache**
   - Cache directory listings for repeated runs
   - Useful for incremental processing

3. **Symlink detection and handling**
   - Skip symlinks to avoid infinite loops
   - Add option to follow symlinks selectively

## Implementation Priority

### Priority 1 (Immediate impact)
- Modify `os.walk()` to skip excluded directories
- Add early directory exclusion check
- Add depth limiting option

### Priority 2 (Performance tuning)
- Optimize file filtering logic
- Add parallel processing option
- Implement lazy file reading

### Priority 3 (Advanced features)
- Symlink handling
- Directory caching
- Path operation optimization

## Expected Performance Gains

- **Directory pruning:** 50-90% reduction in execution time for projects with large excluded directories
- **Depth limiting:** Prevents infinite loops, ensures bounded execution time
- **Early filtering:** 10-30% reduction in file processing overhead
- **Parallel processing:** 2-4x speedup on multi-core systems (depending on I/O bottlenecks)

## Testing Strategy

1. Create test cases with deep nested directories
2. Benchmark current performance vs. optimized versions
3. Test with various excluded directory configurations
4. Verify correctness of output remains unchanged
5. Test edge cases (symlinks, permissions, very deep nesting)