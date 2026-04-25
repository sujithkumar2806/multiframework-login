// dotnet-server/Program.cs
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Npgsql;
using System.Text.Json;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddCors();
var app = builder.Build();

app.UseCors(x => x.AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader());

string connectionString = "Host=postgres;Database=userdb;Username=admin;Password=secretpassword";

app.MapGet("/api/health", () => Results.Json(new { status = "healthy", framework = ".NET 🚀" }));

app.MapPost("/api/register", async (HttpContext context) =>
{
    var data = await JsonSerializer.DeserializeAsync<RegisterData>(context.Request.Body);
    
    using var conn = new NpgsqlConnection(connectionString);
    await conn.OpenAsync();
    
    // Check if user exists
    var checkCmd = new NpgsqlCommand("SELECT id FROM users WHERE username = @username OR email = @email", conn);
    checkCmd.Parameters.AddWithValue("@username", data.Username);
    checkCmd.Parameters.AddWithValue("@email", data.Email);
    
    if (await checkCmd.ExecuteScalarAsync() != null)
        return Results.BadRequest(new { message = "Username or email already exists" });
    
    // Hash password and insert
    string hashedPassword = BCrypt.Net.BCrypt.HashPassword(data.Password);
    var insertCmd = new NpgsqlCommand("INSERT INTO users (username, email, password_hash) VALUES (@username, @email, @password) RETURNING username", conn);
    insertCmd.Parameters.AddWithValue("@username", data.Username);
    insertCmd.Parameters.AddWithValue("@email", data.Email);
    insertCmd.Parameters.AddWithValue("@password", hashedPassword);
    
    var result = await insertCmd.ExecuteScalarAsync();
    return Results.Json(new { message = "User created successfully", username = result });
});

app.MapPost("/api/login", async (HttpContext context) =>
{
    var data = await JsonSerializer.DeserializeAsync<LoginData>(context.Request.Body);
    
    using var conn = new NpgsqlConnection(connectionString);
    await conn.OpenAsync();
    
    var cmd = new NpgsqlCommand("SELECT username, password_hash FROM users WHERE username = @username OR email = @username", conn);
    cmd.Parameters.AddWithValue("@username", data.Username);
    
    using var reader = await cmd.ExecuteReaderAsync();
    if (!await reader.ReadAsync())
        return Results.Unauthorized();
    
    string username = reader.GetString(0);
    string storedHash = reader.GetString(1);
    
    if (!BCrypt.Net.BCrypt.Verify(data.Password, storedHash))
        return Results.Unauthorized();
    
    return Results.Json(new { message = "Login successful", username = username });
});

app.Run("http://0.0.0.0:8080");

record RegisterData(string Username, string Email, string Password);
record LoginData(string Username, string Password);
