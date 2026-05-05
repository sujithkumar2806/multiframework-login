using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.DependencyInjection;
using Npgsql;
using System.Text.Json;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddCors();
var app = builder.Build();

app.UseCors(x => x.AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader());

string host = Environment.GetEnvironmentVariable("DB_HOST") ?? "multiframework-db.c4fuy0s4wc4o.us-east-1.rds.amazonaws.com";
string port = Environment.GetEnvironmentVariable("DB_PORT") ?? "5432";
string database = Environment.GetEnvironmentVariable("DB_NAME") ?? "postgres";
string username = Environment.GetEnvironmentVariable("DB_USER") ?? "dbadmin";
string password = Environment.GetEnvironmentVariable("DB_PASSWORD") ?? "SecurePass123!";

string connectionString = $"Host={host};Port={port};Database={database};Username={username};Password={password};SSL Mode=Require;Trust Server Certificate=true";

// Health check endpoints
app.MapGet("/health", () => Results.Json(new { status = "healthy", framework = ".NET 🚀" }));
app.MapGet("/api/health", () => Results.Json(new { status = "healthy", framework = ".NET 🚀" }));
app.MapGet("/metrics", () => "# No metrics yet\n");

app.MapPost("/api/register", async (HttpContext context) =>
{
    try
    {
        // Read as dictionary to handle both camelCase and PascalCase
        var dict = await JsonSerializer.DeserializeAsync<Dictionary<string, string>>(context.Request.Body);
        
        if (dict == null || !dict.ContainsKey("username"))
        {
            return Results.BadRequest(new { error = "Username required" });
        }
        
        string reqUsername = dict["username"];
        string reqEmail = dict.ContainsKey("email") ? dict["email"] : reqUsername + "@example.com";
        string reqPassword = dict.ContainsKey("password") ? dict["password"] : "";
        
        if (string.IsNullOrEmpty(reqPassword))
        {
            return Results.BadRequest(new { error = "Password required" });
        }
        
        using var conn = new NpgsqlConnection(connectionString);
        await conn.OpenAsync();
        
        // Check if user exists
        using var checkCmd = new NpgsqlCommand("SELECT id FROM users WHERE username = @username OR email = @email", conn);
        checkCmd.Parameters.AddWithValue("@username", reqUsername);
        checkCmd.Parameters.AddWithValue("@email", reqEmail);
        
        if (await checkCmd.ExecuteScalarAsync() != null)
            return Results.BadRequest(new { message = "Username already exists" });
        
        // Hash password with bcrypt
        string hashedPassword = BCrypt.Net.BCrypt.HashPassword(reqPassword, 12);
        
        using var insertCmd = new NpgsqlCommand("INSERT INTO users (username, email, password_hash) VALUES (@username, @email, @password) RETURNING username", conn);
        insertCmd.Parameters.AddWithValue("@username", reqUsername);
        insertCmd.Parameters.AddWithValue("@email", reqEmail);
        insertCmd.Parameters.AddWithValue("@password", hashedPassword);
        
        var result = await insertCmd.ExecuteScalarAsync();
        return Results.Json(new { message = "User created successfully", username = result });
    }
    catch (Exception ex)
    {
        Console.WriteLine($"Register error: {ex.Message}");
        return Results.Json(new { error = ex.Message }, statusCode: 500);
    }
});

app.MapPost("/api/login", async (HttpContext context) =>
{
    try
    {
        // Read as dictionary to handle both camelCase and PascalCase
        var dict = await JsonSerializer.DeserializeAsync<Dictionary<string, string>>(context.Request.Body);
        
        if (dict == null || !dict.ContainsKey("username") || !dict.ContainsKey("password"))
        {
            return Results.BadRequest(new { message = "Username and password required" });
        }
        
        string reqUsername = dict["username"];
        string reqPassword = dict["password"];
        
        using var conn = new NpgsqlConnection(connectionString);
        await conn.OpenAsync();
        
        using var cmd = new NpgsqlCommand("SELECT username, password_hash FROM users WHERE username = @username OR email = @username", conn);
        cmd.Parameters.AddWithValue("@username", reqUsername);
        
        using var reader = await cmd.ExecuteReaderAsync();
        if (!await reader.ReadAsync())
            return Results.Json(new { message = "Invalid credentials" }, statusCode: 401);
        
        string responseUsername = reader.GetString(0);
        string storedHash = reader.GetString(1);
        
        if (!BCrypt.Net.BCrypt.Verify(reqPassword, storedHash))
            return Results.Json(new { message = "Invalid credentials" }, statusCode: 401);
        
        return Results.Json(new { message = "Login successful", username = responseUsername });
    }
    catch (Exception ex)
    {
        Console.WriteLine($"Login error: {ex.Message}");
        return Results.Json(new { error = ex.Message }, statusCode: 500);
    }
});

app.MapGet("/metrics", () => Results.Text(@"
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{framework=""dotnet"",method=""GET"",endpoint=""/api/health""} 0
# HELP up Was the last scrape of .NET successful
# TYPE up gauge
up{job=""dotnet-backend""} 1
", "text/plain"));

app.Run("http://0.0.0.0:8080");
