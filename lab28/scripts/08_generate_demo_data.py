#!/usr/bin/env python3
"""Generate rich demo dataset for the platform.
Creates 50 diverse Vietnamese + English documents for the data pipeline demo.
"""
import json, time, os, random

DEMO_RECORDS = [
    # Vietnamese records
    {"id": "vn_001", "text": "Trí tuệ nhân tạo đang thay đổi cách doanh nghiệp Việt Nam vận hành. AI platform giúp tự động hóa quy trình từ data ingestion đến model serving.", "lang": "vi", "category": "ai"},
    {"id": "vn_002", "text": "Platform engineering là phương pháp xây dựng nền tảng nội bộ cho developers. Mục tiêu là giảm cognitive load và tăng developer velocity.", "lang": "vi", "category": "engineering"},
    {"id": "vn_003", "text": "Kafka là message broker phân tán dùng để xây dựng data pipeline real-time. Kafka có khả năng xử lý hàng triệu events mỗi giây.", "lang": "vi", "category": "data"},
    {"id": "vn_004", "text": "Vector database như Qdrant cho phép tìm kiếm semantic similarity. Embedding models chuyển văn bản thành vectors trong không gian nhiều chiều.", "lang": "vi", "category": "data"},
    {"id": "vn_005", "text": "Feast là feature store open-source cho machine learning. Nó quản lý feature definitions, offline storage, và online serving cho real-time inference.", "lang": "vi", "category": "ml"},
    {"id": "vn_006", "text": "Observability với Prometheus và Grafana giúp monitor toàn bộ AI platform. Metrics, logs, traces là ba trụ cột của observability.", "lang": "vi", "category": "ops"},
    {"id": "vn_007", "text": "MLflow theo dõi experiments, model versions, và metrics trong quá trình training. Model registry lưu trữ và quản lý các phiên bản model.", "lang": "vi", "category": "ml"},
    {"id": "vn_008", "text": "DVC (Data Version Control) giống như Git cho datasets và ML models. Nó cho phép reproducibility trong ML pipelines.", "lang": "vi", "category": "ml"},
    {"id": "vn_009", "text": "GitHub Actions CI/CD tự động hóa testing, building, và deployment. Mỗi pull request chạy smoke tests để đảm bảo chất lượng.", "lang": "vi", "category": "ops"},
    {"id": "vn_010", "text": "RBAC (Role-Based Access Control) phân quyền người dùng trong hệ thống. Admin có toàn quyền, viewer chỉ được đọc dữ liệu.", "lang": "vi", "category": "governance"},
    {"id": "vn_011", "text": "PII (Personally Identifiable Information) cần được bảo vệ trong data pipelines. Masking và encryption là hai kỹ thuật phổ biến.", "lang": "vi", "category": "governance"},
    {"id": "vn_012", "text": "AES-256-GCM là thuật toán mã hóa đối xứng được sử dụng rộng rãi. Nó cung cấp cả confidentiality và integrity.", "lang": "vi", "category": "governance"},
    {"id": "vn_013", "text": "Circuit breaker pattern ngăn chặn cascading failures trong distributed systems. Khi service bị lỗi liên tục, circuit mở ra để bảo vệ hệ thống.", "lang": "vi", "category": "engineering"},
    {"id": "vn_014", "text": "Delta Lake là storage layer open-source cho data lakes. Nó cung cấp ACID transactions, schema enforcement, và time travel.", "lang": "vi", "category": "data"},
    {"id": "vn_015", "text": "Prefect là workflow orchestration tool cho data pipelines. Prefect hỗ trợ scheduling, retries, và monitoring cho các tasks.", "lang": "vi", "category": "data"},
    {"id": "vn_016", "text": "vLLM là inference engine hiệu năng cao cho large language models. Nó sử dụng PagedAttention để tối ưu memory usage.", "lang": "vi", "category": "compute"},
    {"id": "vn_017", "text": "GPU T4 của NVIDIA phù hợp cho inference tasks với chi phí hợp lý. Memory bandwidth và CUDA cores quyết định hiệu năng inference.", "lang": "vi", "category": "compute"},
    {"id": "vn_018", "text": "FPT Cloud AI Factory cung cấp GPU infrastructure và API cho AI workloads. Hỗ trợ Llama, Qwen, DeepSeek và nhiều model khác.", "lang": "vi", "category": "compute"},
    {"id": "vn_019", "text": "LangSmith giúp tracing và debugging LLM applications. Nó capture inputs, outputs, latency, và token usage của mỗi request.", "lang": "vi", "category": "ops"},
    {"id": "vn_020", "text": "Compliance automation đảm bảo hệ thống tuân thủ các quy định về bảo mật dữ liệu. Audit logs ghi lại mọi hành động trong hệ thống.", "lang": "vi", "category": "governance"},

    # English records
    {"id": "en_001", "text": "Artificial Intelligence platforms are transforming how enterprises build and deploy ML models. The end-to-end pipeline from data ingestion to model serving requires robust infrastructure.", "lang": "en", "category": "ai"},
    {"id": "en_002", "text": "Platform engineering is the discipline of designing and building internal developer platforms. It reduces cognitive load on development teams while increasing delivery velocity.", "lang": "en", "category": "engineering"},
    {"id": "en_003", "text": "Apache Kafka is a distributed event streaming platform capable of handling trillions of events per day. It forms the backbone of many real-time data pipelines.", "lang": "en", "category": "data"},
    {"id": "en_004", "text": "Vector databases enable semantic search by storing embeddings. Qdrant, Pinecone, and Weaviate are popular choices for RAG (Retrieval Augmented Generation) systems.", "lang": "en", "category": "data"},
    {"id": "en_005", "text": "Feature stores like Feast bridge the gap between data engineering and ML. They ensure consistency between training and serving features in production.", "lang": "en", "category": "ml"},
    {"id": "en_006", "text": "The three pillars of observability are metrics, logs, and traces. Prometheus handles metrics, Loki handles logs, and Jaeger handles distributed tracing.", "lang": "en", "category": "ops"},
    {"id": "en_007", "text": "MLflow provides experiment tracking, model registry, and deployment tools. It helps data scientists maintain reproducibility across training runs.", "lang": "en", "category": "ml"},
    {"id": "en_008", "text": "DVC brings version control to ML projects. Like Git for code, DVC versions datasets and models, enabling full reproducibility of experiments.", "lang": "en", "category": "ml"},
    {"id": "en_009", "text": "CI/CD pipelines with GitHub Actions automate the software delivery process. Every commit triggers tests, builds, and deployments automatically.", "lang": "en", "category": "ops"},
    {"id": "en_010", "text": "Role-Based Access Control defines permissions based on user roles. The principle of least privilege ensures users only access what they need.", "lang": "en", "category": "governance"},
    {"id": "en_011", "text": "PII detection and masking are critical for data privacy compliance. Regulations like GDPR require organizations to protect personal data.", "lang": "en", "category": "governance"},
    {"id": "en_012", "text": "AES-256 encryption provides military-grade data protection. When combined with proper key management, it ensures data confidentiality at rest and in transit.", "lang": "en", "category": "governance"},
    {"id": "en_013", "text": "The circuit breaker pattern prevents cascading failures in microservices. When downstream services fail repeatedly, the circuit opens to protect the upstream system.", "lang": "en", "category": "engineering"},
    {"id": "en_014", "text": "Delta Lake provides ACID transactions on top of data lakes. Built on Apache Parquet, it enables reliable data pipelines with schema enforcement.", "lang": "en", "category": "data"},
    {"id": "en_015", "text": "Prefect is a modern workflow orchestration platform. Unlike Airflow, it supports dynamic DAGs and has first-class Python support.", "lang": "en", "category": "data"},
    {"id": "en_016", "text": "vLLM achieves state-of-the-art LLM serving throughput through PagedAttention. It efficiently manages KV cache memory for high-concurrency inference.", "lang": "en", "category": "compute"},
    {"id": "en_017", "text": "GPU computing accelerates ML workloads by orders of magnitude. NVIDIA T4, A100, and H100 GPUs offer different price-performance trade-offs.", "lang": "en", "category": "compute"},
    {"id": "en_018", "text": "Cloud AI platforms democratize access to GPU infrastructure. FPT Cloud, AWS SageMaker, and Google Vertex AI provide managed ML services.", "lang": "en", "category": "compute"},
    {"id": "en_019", "text": "LLM observability tools like LangSmith help debug and optimize LLM applications. They provide visibility into prompt chains, token usage, and response quality.", "lang": "en", "category": "ops"},
    {"id": "en_020", "text": "Compliance automation reduces the burden of regulatory requirements. Automated audit trails, data retention policies, and access reviews are essential.", "lang": "en", "category": "governance"},
    {"id": "en_021", "text": "RAG (Retrieval Augmented Generation) combines vector search with LLM generation. It enables LLMs to answer questions based on external knowledge bases.", "lang": "en", "category": "ai"},
    {"id": "en_022", "text": "Event-driven architectures decouple services through asynchronous messaging. This pattern improves resilience and scalability of distributed systems.", "lang": "en", "category": "engineering"},
    {"id": "en_023", "text": "Data lineage tracks the journey of data through pipelines. Tools like OpenLineage integrate with Prefect and Airflow for end-to-end visibility.", "lang": "en", "category": "data"},
    {"id": "en_024", "text": "Model serving frameworks handle inference requests at scale. Options range from managed APIs (FPT Cloud) to self-hosted solutions (vLLM, TGI).", "lang": "en", "category": "compute"},
    {"id": "en_025", "text": "Chaos engineering tests system resilience through controlled failures. By breaking things intentionally, teams learn how systems behave under stress.", "lang": "en", "category": "ops"},
    {"id": "en_026", "text": "Fine-tuning adapts pre-trained models to specific domains. LoRA (Low-Rank Adaptation) is an efficient fine-tuning technique that reduces memory requirements.", "lang": "en", "category": "ml"},
    {"id": "en_027", "text": "API gateways serve as the single entry point for client requests. They handle authentication, rate limiting, routing, and circuit breaking.", "lang": "en", "category": "engineering"},
    {"id": "en_028", "text": "Prompt engineering is the practice of designing effective prompts for LLMs. Well-crafted prompts significantly improve response quality and relevance.", "lang": "en", "category": "ml"},
    {"id": "en_029", "text": "Kubernetes orchestrates containerized applications at scale. GPU node pools with auto-scaling optimize resource utilization for ML workloads.", "lang": "en", "category": "compute"},
    {"id": "en_030", "text": "Production readiness requires comprehensive testing. Smoke tests, integration tests, and chaos tests validate that systems are ready for production traffic.", "lang": "en", "category": "ops"},
]

def main():
    output_file = "outputs/demo_dataset.json"
    os.makedirs("outputs", exist_ok=True)

    # Add timestamps
    for r in DEMO_RECORDS:
        r["timestamp"] = time.time()

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(DEMO_RECORDS, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(DEMO_RECORDS)} demo records")
    print(f"  Vietnamese: {sum(1 for r in DEMO_RECORDS if r['lang'] == 'vi')}")
    print(f"  English:    {sum(1 for r in DEMO_RECORDS if r['lang'] == 'en')}")
    print(f"  Categories: ai={sum(1 for r in DEMO_RECORDS if r['category']=='ai')}, "
          f"engineering={sum(1 for r in DEMO_RECORDS if r['category']=='engineering')}, "
          f"data={sum(1 for r in DEMO_RECORDS if r['category']=='data')}, "
          f"ml={sum(1 for r in DEMO_RECORDS if r['category']=='ml')}, "
          f"ops={sum(1 for r in DEMO_RECORDS if r['category']=='ops')}, "
          f"compute={sum(1 for r in DEMO_RECORDS if r['category']=='compute')}, "
          f"governance={sum(1 for r in DEMO_RECORDS if r['category']=='governance')}")
    print(f"  Saved to: {output_file}")
    return DEMO_RECORDS

if __name__ == "__main__":
    records = main()
