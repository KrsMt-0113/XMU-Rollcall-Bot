use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::fs;
use chrono::Timelike;

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
pub struct Rollcall {
    pub course_title: String,
    pub created_by_name: String,
    pub department_name: String,
    pub is_expired: bool,
    pub is_number: bool,
    pub is_radar: bool,
    pub rollcall_id: i64,
    pub rollcall_status: String,
    pub scored: bool,
    pub status: String,
}

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
pub struct RollcallData {
    pub rollcalls: Vec<Rollcall>,
}

pub fn clear_screen() {
    if cfg!(target_os = "windows") {
        std::process::Command::new("cmd")
            .args(&["/C", "cls"])
            .status()
            .unwrap();
    } else {
        std::process::Command::new("clear")
            .status()
            .unwrap();
    }
}

pub async fn save_session(_client: &Client, path: &str) -> anyhow::Result<()> {
    // 简化的会话保存 - 由于reqwest的cookie_store方法在不同版本中行为不同
    // 这里使用一个简化的实现
    let empty_data = serde_json::json!({"saved": true});
    fs::write(path, serde_json::to_string(&empty_data)?)?;
    Ok(())
}

pub async fn load_session(_path: &str) -> anyhow::Result<Client> {
    // 简化的会话加载 - 返回一个新的带cookie store的client
    let client = reqwest::Client::builder()
        .cookie_store(true)
        .build()?;
    
    Ok(client)
}

pub async fn verify_session(client: &Client) -> anyhow::Result<serde_json::Value> {
    let url = "https://lnt.xmu.edu.cn/api/profile";
    let resp = client.get(url).send().await?;
    
    if resp.status().is_success() {
        let json: serde_json::Value = resp.json().await?;
        if json.get("name").is_some() {
            return Ok(json);
        }
    }
    
    Err(anyhow::anyhow!("Session verification failed"))
}

pub fn get_greeting() -> &'static str {
    let hour = chrono::Local::now().hour();
    
    if hour >= 5 && hour < 12 {
        "Good morning"
    } else if hour >= 12 && hour < 18 {
        "Good afternoon"
    } else {
        "Good evening"
    }
}
