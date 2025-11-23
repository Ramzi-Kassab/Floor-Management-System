# Migration Issues & Solutions

## Status
Migrations are partially working but have some circular dependency and field reference issues between inventory and engineering apps due to a model refactoring where models were moved from inventory to engineering.

## Issues Found
1. Circular dependency between engineering.0001 and inventory.0005
2. Missing index/constraint removals before field removals
3. ForeignKey reference resolution issues during AlterField operations

## Fixes Applied
- Removed circular dependency by removing engineering dependency from inventory.0005
- Added RemoveIndex operations for: ix_bd_level_size, ix_bdr_design_active, ix_bdr_design_type
- Added RemoveConstraint operation for: uq_bdr_design_revision

## Remaining Issues
- AlterField operations referencing engineering models before engineering migrations run
- Need to use SeparateDatabaseAndState operations for proper model migration between apps

## Workaround for Development
Use `python manage.py migrate --fake` to mark migrations as applied, then manually create database schema using Django's ORM or fixtures.

## Files Modified
- floor_app/operations/engineering/migrations/0001_initial.py
- floor_app/operations/inventory/migrations/0005_remove_bitdesign_created_by_remove_bitdesign_level_and_more.py

## Next Steps
- Use management commands to create sample data
- Focus on frontend development
- Return to migration fixes as separate task if needed
