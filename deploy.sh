version: 0.2

phases:
  install:
    commands:
      - echo "Installing dependencies..."
      - pip install -r requirements.txt
  pre_build:
    commands:
      - echo "Setting up environment variables and retrieving secrets..."
      # (Any commands to set up your environment go here)
  build:
    commands:
      - echo "Running deployment script..."
      - chmod +x deploy.sh
      - ./deploy.sh

artifacts:
  files:
    - "**/*"
