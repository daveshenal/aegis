terraform {
  required_version = ">= 1.8.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Remote state — stored in the S3 bucket you created manually
  backend "s3" {
    bucket = "agentic-research-tfstate"
    key    = "prod/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

module "ecr" {
  source    = "./modules/ecr"
  repo_name = var.ecr_repo_name
}

module "iam" {
  source      = "./modules/iam"
  bucket_name = var.s3_bucket_name
  project     = var.project_name
}

module "s3" {
  source      = "./modules/s3"
  bucket_name = var.s3_bucket_name
}

module "ecs" {
  source             = "./modules/ecs"
  project            = var.project_name
  aws_region         = var.aws_region
  ecr_image_uri      = "${module.ecr.repository_url}:latest"
  task_role_arn      = module.iam.task_role_arn
  execution_role_arn = module.iam.execution_role_arn
  s3_bucket_name     = var.s3_bucket_name
}