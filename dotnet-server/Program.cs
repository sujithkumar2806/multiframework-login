using Microsoft.AspNetCore.Mvc;
using Npgsql;
using System.Text;
using Microsoft.AspNetCore.Cors;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll", policy =>
    {
        policy.AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader();
    });
});
builder.Services.AddEndpointsApiExplorer();

var app = builder.Build();
app.UseCors("AllowAll");

var connectionString = Environment.GetEnvironmentVariable("DATABASE_URL") ?? 
    "Host=multiframework-db.c4fuy0s4wc4o.us-east-1.rds.amazonaws.com;Database=postgres;Username=dbadmin;Password=SecurePass123!";

app.MapGet("/health", () => Results.Ok(new { status = "healthy", framework = ".NET 🚀" }));

app.MapPost("/api/register", async ([FromBody] User user) =>
{
    try
    {
        using var conn = new NpgsqlConnection(connectionString);
        await conn.OpenAsync();
        
        string hashedPassword = BCrypt.Net.BCrypt.HashPassword(user.Password, 12);
        
        using var cmd = new NpgsqlCommand(
            "INSERT INTO users (username, email, password_hash) VALUES (@username, @email, @hash)", conn);
        cmd.Parameters.AddWithValue("@username", user.Username);
        cmd.Parameters.AddWithValue("@email", user.Email);
        cmd.Parameters.AddWithValue("@hash", hashedPassword);
        
        await cmd.ExecuteNonQueryAsync();
        return Results.Ok(new { message = "User created successfully", username = user.Username });
    }
    catch (Exception ex)
    {
        return Results.BadRequest(new { error = ex.Message });
    }
});

app.MapPost("/api/login", async ([FromBody] LoginRequest login) =>
{
    try
    {
        using var conn = new NpgsqlConnection(connectionString);
        await conn.OpenAsync();
        
        using var cmd = new NpgsqlCommand(
            "SELECT username, email, password_hash FROM users WHERE username = @username OR email = @username", conn);
        cmd.Parameters.AddWithValue("@username", login.Username);
        
        using var reader = await cmd.ExecuteReaderAsync();
        
        if (!await reader.ReadAsync())
            return Results.Unauthorized(new { message = "Invalid credentials" });
        
        string storedHash = reader.GetString(2);
        
        if (!BCrypt.Net.BCrypt.Verify(login.Password, storedHash))
            return Results.Unauthorized(new { message = "Invalid credentials" });
        
        return Results.Ok(new { message = "Login successful", username = reader.GetString(0) });
    }
    catch (Exception ex)
    {
        return Results.BadRequest(new { error = ex.Message });
    }
});

app.Run();

record User(string Username, string Email, string Password);
record LoginRequest(string Username, string Password);
