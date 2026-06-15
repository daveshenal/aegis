variable "project"             { type = string }
variable "aws_region"          { type = string }
variable "ecr_image_uri"       { type = string }
variable "task_role_arn"       { type = string }
variable "execution_role_arn"  { type = string }
variable "s3_bucket_name"      { type = string }

# CloudWatch log group — all container stdout goes here
resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${var.project}"
  retention_in_days = 30
}

# ECS Cluster — logical grouping of tasks
resource "aws_ecs_cluster" "this" {
  name = "${var.project}-cluster"
}

# Task Definition — describes the container: image, CPU, RAM, env vars, logging
resource "aws_ecs_task_definition" "app" {
  family                   = "${var.project}-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  task_role_arn            = var.task_role_arn
  execution_role_arn       = var.execution_role_arn

  container_definitions = jsonencode([{
    name      = "${var.project}-container"
    image     = var.ecr_image_uri
    essential = true

    portMappings = [{
      containerPort = 8000
      protocol      = "tcp"
    }]

    # Secrets are injected as environment variables at runtime by ECS
    # In production these come from AWS Secrets Manager or SSM Parameter Store
    # For now we reference them as plain env vars - you will update this later
    environment = [
      { name = "S3_BUCKET_NAME",        value = var.s3_bucket_name },
      { name = "AWS_REGION",            value = var.aws_region },
      { name = "LANGCHAIN_TRACING_V2",  value = "true" },
      { name = "LANGCHAIN_PROJECT",     value = "aegis" },
      { name = "MAX_REVISIONS",         value = "3" },
      { name = "MLFLOW_TRACKING_URI",   value = "http://localhost:5000" },
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.app.name
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = "ecs"
      }
    }
  }])
}

# Use default VPC and subnets — fine for a portfolio project
data "aws_vpc" "default" { default = true }

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Security group — allow inbound on 8000, allow all outbound
resource "aws_security_group" "app" {
  name   = "${var.project}-sg"
  vpc_id = data.aws_vpc.default.id

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ECS Service — keeps 1 task running at all times, restarts on failure
resource "aws_ecs_service" "app" {
  name            = "${var.project}-service"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups  = [aws_security_group.app.id]
    assign_public_ip = true
  }

  # Allow deployment without downtime — new task starts before old one stops
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
}

output "cluster_name" { value = aws_ecs_cluster.this.name }
output "service_name"  { value = aws_ecs_service.app.name }