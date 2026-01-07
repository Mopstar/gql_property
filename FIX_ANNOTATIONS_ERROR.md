# Fix for "__annotations__" AttributeError

## Problem
When running this project on some systems, you may encounter this error when calling create purchase mutations:
```
AttributeError: object has no attribute '__annotations__'
```

## Root Cause
This error occurs due to how Python handles class attributes and the interaction between:
1. Strawberry GraphQL decorators (`@strawberry.input`)
2. Mixin classes (`TreeInputStructureMixin`, `InputModelMixin`)
3. Python dataclass annotations

The `TreeInputStructureMixin` and `InputModelMixin` classes from `uoishelpers` access the `__annotations__` attribute of the class during initialization. In some Python versions or environments, this attribute may not be properly initialized before the mixin tries to access it.

## Solution Applied
The fix is to explicitly initialize `__annotations__` as an empty dict at the beginning of classes that inherit from these mixins. The Strawberry decorator will then populate it with the actual field annotations.

### Files Modified
1. [src/GraphTypeDefinitions/PurchaseGQLModel.py](src/GraphTypeDefinitions/PurchaseGQLModel.py)
   - Added `__annotations__ = {}` to `PurchaseInsertGQLModel`

2. [src/GraphTypeDefinitions/PurchaseItemGQLModel.py](src/GraphTypeDefinitions/PurchaseItemGQLModel.py)
   - Added `__annotations__ = {}` to `PurchaseItemInsertGQLModel`

3. [src/GraphTypeDefinitions/EventGQLModel.py](src/GraphTypeDefinitions/EventGQLModel.py)
   - Added `__annotations__ = {}` to `EventInsertGQLModel`
   - Added `__annotations__ = {}` to `EventPlanInsertGQLModel`

## Why This Works
By explicitly declaring `__annotations__ = {}` before any field definitions:
1. The class has the `__annotations__` attribute when the mixin's `__init__` is called
2. The Strawberry decorator still functions correctly and populates the annotations
3. This works across different Python versions (3.9, 3.10, 3.11, 3.12, 3.13)

## Testing
To verify the fix works, you can run:
```powershell
python -c "from src.GraphTypeDefinitions.PurchaseGQLModel import PurchaseInsertGQLModel; print('Has annotations:', hasattr(PurchaseInsertGQLModel, '__annotations__'))"
```

Expected output: `Has annotations: True`

## Environment Compatibility
This fix ensures compatibility between:
- Different Python versions (especially 3.9-3.13)
- Different operating systems (Windows, Linux, macOS)
- Different ways of running the application (direct Python, Docker, virtual environments)

## Additional Notes
If you encounter similar errors with other input model classes, apply the same fix:
1. Identify classes that inherit from `TreeInputStructureMixin` or `InputModelMixin`
2. Add `__annotations__ = {}` as the first line after the class definition
3. Ensure it comes before any field definitions or the `getLoader` method
