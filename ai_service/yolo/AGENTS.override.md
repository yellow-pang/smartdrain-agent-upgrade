# YOLO area override

This directory is owned by another team member and contains a temporary legacy PoC model.

Default rule: treat `yolo/**` as read-only.

Do not:

- retrain or replace `models/best.pt`
- change class semantics without an explicit team decision
- make XGBoost import this module
- add XGBoost business logic here

Only edit this directory when the user explicitly asks for YOLO adapter or temporary inference changes. Preserve the output contract in `shared/contracts/yolo_result.schema.json`.
