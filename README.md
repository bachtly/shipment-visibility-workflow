# Shipment visibility system
An demo app to show case the application of DBOS & IaC to implement a portal of shipment journey visibility. The status changes in real life are supposed to be events from webhooks, but should simply be an endpoint and triggered via a button in this example.

## Main requirements
- There is a UI (buttons) to simulate a webhook event from a vendor
- There is UI to show shipping progress
- Workflow management using DBOS
- Have IaC with provider Azure
- Infra should make use of serverless or scalable solutions like container apps
- Infra should separate dev and staging, could use terragrunt if needed
- Infra should follow best practice of production

## Environment
DBOS Conductor API key: dbos_e5702f9e-47c9-4311-80fc-db7fcd8e8994_7f744b81-944b-415c-b3bb-35828db9d67b
DBOS Conductor app name: shipment-visibility