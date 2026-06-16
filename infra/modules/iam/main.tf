# Trust policy — allows ECS tasks to assume this role
data "aws_iam_policy_document" "ecs_trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

# Task role — permissions your application code uses at runtime
resource "aws_iam_role" "task_role" {
  name               = "${var.project}-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_trust.json
}

resource "aws_iam_role_policy" "s3_access" {
  name = "${var.project}-s3-access"
  role = aws_iam_role.task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]
      Resource = [
        "arn:aws:s3:::${var.bucket_name}",
        "arn:aws:s3:::${var.bucket_name}/*"
      ]
    }]
  })
}

# Execution role — permissions ECS itself uses to pull image and push logs
resource "aws_iam_role" "execution_role" {
  name               = "${var.project}-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_trust.json
}

resource "aws_iam_role_policy_attachment" "execution_policy" {
  role       = aws_iam_role.execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "ssm_access" {
  name = "${var.project}-ssm-access"
  role = aws_iam_role.execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ssm:GetParameters",
        "ssm:GetParameter"
      ]
      Resource = "arn:aws:ssm:us-east-1:410376035918:parameter/aegis/*"
    }]
  })
}