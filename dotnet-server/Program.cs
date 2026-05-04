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

app.MapGet("/api/health", () => Results.Json(new { status = "healthy", framework = ".NET 🚀" }));

app.MapPost("/api/register", async (HttpContext context) =>
{
    try
    {
        var data = await JsonSerializer.DeserializeAsync<RegisterData>(context.Request.Body);
        
        if (data == null || string.IsNullOrEmpty(data.Username))
        {
            return Results.BadRequest(new { error = "Invalid request data" });
        }
        
        using var conn = new NpgsqlConnection(connectionString);
        await conn.OpenAsync();
        
        // Check if user exists
        using var checkCmd = new NpgsqlCommand("SELECT id FROM users WHERE username = @username OR email = @email", conn);
        checkCmd.Parameters.AddWithValue("@username", data.Username);
        checkCmd.Parameters.AddWithValue("@email", data.Email);
        
        if (await checkCmd.ExecuteScalarAsync() != null)
            return Results.BadRequest(new { message = "Username or email already exists" });
        
        // Hash password with bcrypt
        string hashedPassword = BCrypt.Net.BCrypt.HashPassword(data.Password, 12);
        
        using var insertCmd = new NpgsqlCommand("INSERT INTO users (username, email, password_hash) VALUES (@username, @email, @password) RETURNING username", conn);
        insertCmd.Parameters.AddWithValue("@username", data.Username);
        insertCmd.Parameters.AddWithValue("@email", data.Email);
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
        var data = await JsonSerializer.DeserializeAsync<LoginData>(context.Request.Body);
        
        if (data == null || string.IsNullOrEmpty(data.Username))
        {
            return Results.BadRequest(new { error = "Invalid request data" });
        }
        
        using var conn = new NpgsqlConnection(connectionString);
        await conn.OpenAsync();
        
        using var cmd = new NpgsqlCommand("SELECT username, password_hash FROM users WHERE username = @username OR email = @username", conn);
        cmd.Parameters.AddWithValue("@username", data.Username);
        
        using var reader = await cmd.ExecuteReaderAsync();
        if (!await reader.ReadAsync())
            return Results.Json(new { message = "Invalid credentials" }, statusCode: 401);
        
        string responseUsername = reader.GetString(0);
        string storedHash = reader.GetString(1);
        
        if (!BCrypt.Net.BCrypt.Verify(data.Password, storedHash))
            return Results.Json(new { message = "Invalid credentials" }, statusCode: 401);
        
        return Results.Json(new { message = "Login successful", username = responseUsername });
    }
    catch (Exception ex)
    {
        Console.WriteLine($"Login error: {ex.Message}");
        return Results.Json(new { error = ex.Message }, statusCode: 500);
    }
});

app.Run("http://0.0.0.0:8080");

record RegisterData(string Username, string Email, string Password);
record LoginData(string Username, string Password);
