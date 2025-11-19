var builder = DistributedApplication.CreateBuilder(args);

// Add Python FastAPI document processor
// Note: Using AddExecutable to bypass automatic pip install (dependencies managed via uv)
var documentProcessor = builder.AddExecutable(
        "document-processor",
        Path.GetFullPath("../../document-processor/.venv/bin/python"),
        "../../document-processor",
        "main.py")
    .WithHttpEndpoint(port: 8000, env: "PORT")
    .WithExternalHttpEndpoints();

// Add Python FastAPI chunk API
var chunkApi = builder.AddExecutable(
        "chunk-api",
        Path.GetFullPath("../../chunk-api/.venv/bin/python"),
        "../../chunk-api",
        "main.py")
    .WithEnvironment("AZURE_STORAGE_ACCOUNT", "vinfoknowledgedev")
    .WithEnvironment("AZURE_STORAGE_SOURCE_CONTAINER", "vknowledgeuploaddev")
    .WithEnvironment("AZURE_STORAGE_DESTINATION_CONTAINER", "vknowledgechunksdev")
    .WithHttpEndpoint(port: 8001, env: "PORT")
    .WithExternalHttpEndpoints();

// Add Python FastAPI embedding API
var embeddingApi = builder.AddExecutable(
        "embedding-api",
        Path.GetFullPath("../../embedding-api/.venv/bin/python"),
        "../../embedding-api",
        "main.py")
    .WithHttpEndpoint(port: 8002, env: "PORT")
    .WithExternalHttpEndpoints();

// Add Python FastAPI search data API
var searchDataApi = builder.AddExecutable(
        "search-data-api",
        Path.GetFullPath("../../search-data-api/.venv/bin/python"),
        "../../search-data-api",
        "main.py")
    .WithHttpEndpoint(port: 8003, env: "PORT")
    .WithExternalHttpEndpoints();

// Add Python FastAPI graph data API
var graphDataApi = builder.AddExecutable(
        "graph-data-api",
        Path.GetFullPath("../../graph-data-api/.venv/bin/python"),
        "../../graph-data-api",
        "main.py")
    .WithHttpEndpoint(port: 8004, env: "PORT")
    .WithExternalHttpEndpoints();

// Add Next.js knowledge loader
var knowledgeLoader = builder.AddNpmApp("knowledge-loader", "../../knowledge-loader", "dev")
    .WithHttpEndpoint(port: 3000, env: "PORT")
    .WithEnvironment("DOCUMENT_PROCESSOR_URL", documentProcessor.GetEndpoint("http"))
    .WithExternalHttpEndpoints();

// Add Blazor dashboard
var dashboard = builder.AddProject<Projects.DocumentProcessing_Dashboard>("dashboard")
    .WithExternalHttpEndpoints();

builder.Build().Run();
