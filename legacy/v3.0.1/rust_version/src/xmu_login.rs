use aes::Aes128;
use base64::{engine::general_purpose, Engine as _};
use cbc::cipher::{block_padding::Pkcs7, BlockEncryptMut, KeyIvInit};
use rand::Rng;
use regex::Regex;
use reqwest::Client;
use serde_json::Value;

type Aes128CbcEnc = cbc::Encryptor<Aes128>;

const AES_CHARS: &str = "ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678";

fn random_string(n: usize) -> String {
    let mut rng = rand::thread_rng();
    (0..n)
        .map(|_| {
            let idx = rng.gen_range(0..AES_CHARS.len());
            AES_CHARS.chars().nth(idx).unwrap()
        })
        .collect()
}

fn encrypt_password(password: &str, salt: &str) -> String {
    let plaintext = format!("{}{}", random_string(64), password);
    let key = salt.as_bytes();
    let iv = random_string(16);
    let iv_bytes = iv.as_bytes();
    
    let cipher = Aes128CbcEnc::new_from_slices(key, iv_bytes).unwrap();
    let plaintext_bytes = plaintext.as_bytes();

    let encrypted = cipher.encrypt_padded_vec_mut::<Pkcs7>(plaintext_bytes);

    general_purpose::STANDARD.encode(encrypted)
}

pub async fn login_tronclass(username: &str, password: &str) -> anyhow::Result<Client> {
    let url = "https://c-identity.xmu.edu.cn/auth/realms/xmu/protocol/openid-connect/auth";
    let url_2 = "https://c-identity.xmu.edu.cn/auth/realms/xmu/protocol/openid-connect/token";
    let url_3 = "https://lnt.xmu.edu.cn/api/login?login=access_token";

    let client = reqwest::Client::builder()
        .cookie_store(true)
        .redirect(reqwest::redirect::Policy::none())
        .build()?;

    let params = [
        ("scope", "openid"),
        ("response_type", "code"),
        ("client_id", "TronClassH5"),
        ("redirect_uri", "https://c-mobile.xmu.edu.cn/identity-web-login-callback?_h5=true"),
    ];

    let res = client.get(url).query(&params).send().await?;
    let location = res.headers().get("location")
        .ok_or(anyhow::anyhow!("No location header"))?
        .to_str()?;

    let res2 = client.get(location).send().await?;
    let location2 = res2.headers().get("location")
        .ok_or(anyhow::anyhow!("No location header"))?
        .to_str()?;

    let res3 = client.get(location2).send().await?;
    let html = res3.text().await?;

    let salt_re = Regex::new(r#"id="pwdEncryptSalt"\s+value="([^"]+)""#)?;
    let execution_re = Regex::new(r#"name="execution"\s+value="([^"]+)""#)?;

    let salt = salt_re.captures(&html)
        .ok_or(anyhow::anyhow!("Salt not found"))?
        .get(1).unwrap().as_str();
    let execution = execution_re.captures(&html)
        .ok_or(anyhow::anyhow!("Execution not found"))?
        .get(1).unwrap().as_str();

    let enc = encrypt_password(password, salt);

    let form_data = [
        ("username", username),
        ("password", &enc),
        ("captcha", ""),
        ("_eventId", "submit"),
        ("cllt", "userNameLogin"),
        ("dllt", "generalLogin"),
        ("lt", ""),
        ("execution", execution),
    ];

    let res4 = client.post(location2)
        .form(&form_data)
        .send()
        .await?;
    
    let location4 = res4.headers().get("location")
        .ok_or(anyhow::anyhow!("No location header after login"))?
        .to_str()?;

    let res5 = client.get(location4).send().await?;
    let location5 = res5.headers().get("location")
        .ok_or(anyhow::anyhow!("No location header"))?
        .to_str()?;

    let code = location5.split("code=").nth(1)
        .and_then(|s| s.split('&').next())
        .ok_or(anyhow::anyhow!("Code not found"))?;

    let token_form = [
        ("client_id", "TronClassH5"),
        ("grant_type", "authorization_code"),
        ("code", code),
        ("redirect_uri", "https://c-mobile.xmu.edu.cn/identity-web-login-callback?_h5=true"),
        ("scope", "openid"),
    ];

    let res6 = client.post(url_2)
        .form(&token_form)
        .send()
        .await?;
    
    let json: Value = res6.json().await?;
    let access_token = json["access_token"].as_str()
        .ok_or(anyhow::anyhow!("Access token not found"))?;

    let login_data = serde_json::json!({
        "access_token": access_token,
        "org_id": 1
    });

    let res7 = client.post(url_3)
        .json(&login_data)
        .send()
        .await?;

    if res7.status().is_success() {
        Ok(client)
    } else {
        Err(anyhow::anyhow!("Login failed"))
    }
}
