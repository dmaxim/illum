var builder = DistributedApplication.CreateBuilder(args);

// Add Python FastAPI document processor
var documentProcessor = builder.AddPythonApp("document-processor", "../../document-processor", "main.py")
    .WithHttpEndpoint(port: 8000, env: "PORT")
    .WithExternalHttpEndpoints();

// Add Next.js knowledge loader
var knowledgeLoader = builder.AddNpmApp("knowledge-loader", "../../knowledge-loader", "dev")
    .WithHttpEndpoint(port: 3000, env: "PORT")
    .WithExternalHttpEndpoints();

// Add Blazor dashboard
var dashboard = builder.AddProject<Projects.DocumentProcessing_Dashboard>("dashboard")
    .WithExternalHttpEndpoints();

builder.Build().Run();
