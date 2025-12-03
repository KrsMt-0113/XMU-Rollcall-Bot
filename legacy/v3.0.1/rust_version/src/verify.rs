use futures::stream::{self, StreamExt};
use reqwest::Client;
use serde_json::json;
use std::sync::Arc;
use tokio::sync::Mutex;
use uuid::Uuid;

fn pad_number(i: u32) -> String {
    format!("{:04}", i)
}

pub async fn send_code(client: &Client, rollcall_id: i64, _latitude: &str, _longitude: &str) -> bool {
    let url = format!("https://lnt.xmu.edu.cn/api/rollcall/{}/answer_number_rollcall", rollcall_id);
    
    println!("Trying number code...");
    let start = std::time::Instant::now();
    
    let found = Arc::new(Mutex::new(None::<String>));
    let found_clone = Arc::clone(&found);
    
    let client = Arc::new(client.clone());
    
    let tasks = stream::iter(0..10000)
        .map(|i| {
            let url = url.clone();
            let client = Arc::clone(&client);
            let found = Arc::clone(&found);
            
            async move {
                if found.lock().await.is_some() {
                    return None;
                }
                
                let payload = json!({
                    "deviceId": Uuid::new_v4().to_string(),
                    "numberCode": pad_number(i)
                });
                
                match client.put(&url).json(&payload).send().await {
                    Ok(resp) if resp.status().is_success() => {
                        Some(pad_number(i))
                    }
                    _ => None
                }
            }
        })
        .buffer_unordered(200);
    
    tokio::pin!(tasks);
    
    while let Some(result) = tasks.next().await {
        if let Some(code) = result {
            let mut found_lock = found_clone.lock().await;
            if found_lock.is_none() {
                *found_lock = Some(code.clone());
                println!("Number code rollcall answered successfully.");
                println!("Number code: {}", code);
                println!("Time: {:.2} s.", start.elapsed().as_secs_f64());
                return true;
            }
        }
    }
    
    println!("Failed.");
    println!("Time: {:.2} s.", start.elapsed().as_secs_f64());
    false
}

pub async fn send_radar(client: &Client, rollcall_id: i64, latitude: &str, longitude: &str) -> bool {
    let url = format!("https://lnt.xmu.edu.cn/api/rollcall/{}/answer", rollcall_id);
    
    let payload = json!({
        "accuracy": 35,
        "altitude": 0,
        "altitudeAccuracy": null,
        "deviceId": Uuid::new_v4().to_string(),
        "heading": null,
        "latitude": latitude,
        "longitude": longitude,
        "speed": null
    });
    
    match client.put(&url).json(&payload).send().await {
        Ok(resp) if resp.status().is_success() => {
            println!("Radar rollcall answered successfully.");
            true
        }
        _ => false
    }
}

pub async fn process_rollcalls(data: &crate::misc::RollcallData, client: &Client, latitude: &str, longitude: &str) -> crate::misc::RollcallData {
    let count = data.rollcalls.len();
    
    if count == 0 {
        return data.clone();
    }
    
    let now = chrono::Local::now();
    println!("{} New rollcall(s) found!\n", now.format("%H:%M:%S"));
    
    let mut all_success = true;
    
    for (i, rollcall) in data.rollcalls.iter().enumerate() {
        println!("{} of {} :", i + 1, count);
        println!("Course name: {}, rollcall created by {} {}", 
                 rollcall.course_title, rollcall.department_name, rollcall.created_by_name);
        
        let rollcall_type = if rollcall.is_radar {
            "Radar rollcall"
        } else if rollcall.is_number {
            "Number rollcall"
        } else {
            "QRcode rollcall"
        };
        println!("rollcall type: {}\n", rollcall_type);
        
        let success = if rollcall.status == "absent" && rollcall.is_number && !rollcall.is_radar {
            send_code(client, rollcall.rollcall_id, latitude, longitude).await
        } else if rollcall.status == "on_call_fine" {
            println!("Already answered.");
            true
        } else if rollcall.is_radar {
            send_radar(client, rollcall.rollcall_id, latitude, longitude).await
        } else {
            println!("Answering failed.");
            false
        };
        
        if !success {
            all_success = false;
        }
    }
    
    if all_success {
        data.clone()
    } else {
        crate::misc::RollcallData { rollcalls: vec![] }
    }
}
