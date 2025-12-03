mod misc;
mod ui;
mod verify;
mod xmu_login;

use misc::{RollcallData, clear_screen, load_session, save_session, verify_session};
use reqwest::Client;
use std::fs;
use std::time::{Duration, Instant};
use tokio::time::sleep;
use ui::{print_banner, print_dashboard, print_login_status, print_separator, Colors};

const BASE_URL: &str = "https://lnt.xmu.edu.cn";
const INTERVAL: Duration = Duration::from_secs(1);

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let base_dir = std::env::current_dir()?;
    let info_path = base_dir.join("../info.txt");
    let cookies_path = base_dir.join("../cookies.json");

    let info_content = fs::read_to_string(&info_path)
        .expect("Failed to read info.txt");
    let lines: Vec<&str> = info_content.lines().collect();
    
    if lines.len() < 4 {
        eprintln!("info.txt must contain at least 4 lines: username, password, latitude, longitude");
        std::process::exit(1);
    }
    
    let username = lines[0].trim();
    let password = lines[1].trim();
    let latitude = lines[2].trim();
    let longitude = lines[3].trim();

    clear_screen();
    print_banner();
    println!("\n{}Initializing XMU Rollcall Bot...{}\n", Colors::BOLD, Colors::ENDC);
    print_separator("-");

    println!("\n{}[Step 1/3]{} Checking credentials...", Colors::OKCYAN, Colors::ENDC);

    let mut client: Option<Client> = None;

    if cookies_path.exists() {
        println!("{}[Step 2/3]{} Found cached session, attempting to restore...", Colors::OKCYAN, Colors::ENDC);
        
        if let Ok(session_candidate) = load_session(cookies_path.to_str().unwrap()).await {
            if let Ok(_profile) = verify_session(&session_candidate).await {
                client = Some(session_candidate);
                print_login_status("Session restored successfully", true);
            } else {
                print_login_status("Session expired, will re-login", false);
            }
        } else {
            print_login_status("Failed to load session", false);
        }
    }

    if client.is_none() {
        println!("{}[Step 2/3]{} Logging in with credentials...", Colors::OKCYAN, Colors::ENDC);
        sleep(Duration::from_secs(2)).await;
        
        match xmu_login::login_tronclass(username, password).await {
            Ok(session) => {
                let _ = save_session(&session, cookies_path.to_str().unwrap()).await;
                client = Some(session);
                print_login_status("Login successful", true);
            }
            Err(e) => {
                print_login_status(&format!("Login failed: {}", e), false);
                sleep(Duration::from_secs(5)).await;
                std::process::exit(1);
            }
        }
    }

    let client = client.unwrap();

    println!("{}[Step 3/3]{} Fetching user profile...", Colors::OKCYAN, Colors::ENDC);
    let profile = client
        .get(&format!("{}/api/profile", BASE_URL))
        .send()
        .await?
        .json::<serde_json::Value>()
        .await?;
    
    let name = profile["name"].as_str().unwrap_or("User");
    print_login_status(&format!("Welcome, {}", name), true);

    println!("\n{}{}Initialization complete{}", Colors::OKGREEN, Colors::BOLD, Colors::ENDC);
    println!("\n{}Starting monitor in 3 seconds...{}", Colors::GRAY, Colors::ENDC);
    sleep(Duration::from_secs(3)).await;

    let mut temp_data = RollcallData { rollcalls: vec![] };
    let mut query_count = 0u64;
    let start_time = Instant::now();

    print_dashboard(name, start_time, query_count);

    let rollcalls_url = format!("{}/api/radar/rollcalls", BASE_URL);

    let ctrl_c = tokio::signal::ctrl_c();
    tokio::pin!(ctrl_c);

    loop {
        tokio::select! {
            _ = &mut ctrl_c => {
                clear_screen();
                println!("\n{}{}", ui::center_text(&format!("{}Shutting down gracefully...{}", Colors::WARNING, Colors::ENDC)), "");
                println!("{}", ui::center_text(&format!("{}Total queries performed: {}{}", Colors::GRAY, query_count, Colors::ENDC)));
                println!("{}", ui::center_text(&format!("{}Total running time: {}{}", Colors::GRAY, ui::format_time(start_time.elapsed().as_secs()), Colors::ENDC)));
                println!("\n{}\n", ui::center_text(&format!("{}Goodbye{}", Colors::OKGREEN, Colors::ENDC)));
                break;
            }
            _ = sleep(INTERVAL) => {
                match client.get(&rollcalls_url).send().await {
                    Ok(resp) => {
                        if let Ok(data) = resp.json::<RollcallData>().await {
                            query_count += 1;

                            if data.rollcalls != temp_data.rollcalls {
                                temp_data = data.clone();
                                
                                if !temp_data.rollcalls.is_empty() {
                                    clear_screen();
                                    let width = ui::get_terminal_width();
                                    println!("\n{}{}{}{}", Colors::WARNING, Colors::BOLD, "!".repeat(width), Colors::ENDC);
                                    println!("{}", ui::center_text(&format!("{}{}NEW ROLLCALL DETECTED{}", Colors::WARNING, Colors::BOLD, Colors::ENDC)));
                                    println!("{}{}{}{}\n", Colors::WARNING, Colors::BOLD, "!".repeat(width), Colors::ENDC);
                                    
                                    temp_data = verify::process_rollcalls(&temp_data, &client, latitude, longitude).await;
                                    
                                    print_separator("=");
                                    println!("\n{}\n", ui::center_text(&format!("{}Press Ctrl+C to exit, continuing monitor...{}", Colors::GRAY, Colors::ENDC)));
                                    
                                    sleep(Duration::from_secs(3)).await;
                                    print_dashboard(name, start_time, query_count);
                                }
                            }
                        }
                    }
                    Err(e) => {
                        clear_screen();
                        println!("\n{}", ui::center_text(&format!("{}{}Error occurred:{} {}", Colors::FAIL, Colors::BOLD, Colors::ENDC, e)));
                        println!("{}\n", ui::center_text(&format!("{}Exiting...{}", Colors::GRAY, Colors::ENDC)));
                        std::process::exit(1);
                    }
                }
            }
        }
    }

    Ok(())
}
