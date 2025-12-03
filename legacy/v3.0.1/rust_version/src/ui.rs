use crossterm::terminal;

pub struct Colors;

impl Colors {
    pub const HEADER: &'static str = "\x1b[95m";
    pub const OKBLUE: &'static str = "\x1b[94m";
    pub const OKCYAN: &'static str = "\x1b[96m";
    pub const OKGREEN: &'static str = "\x1b[92m";
    pub const WARNING: &'static str = "\x1b[93m";
    pub const FAIL: &'static str = "\x1b[91m";
    pub const ENDC: &'static str = "\x1b[0m";
    pub const BOLD: &'static str = "\x1b[1m";
    pub const UNDERLINE: &'static str = "\x1b[4m";
    pub const GRAY: &'static str = "\x1b[90m";
    pub const WHITE: &'static str = "\x1b[97m";
}

pub fn get_terminal_width() -> usize {
    terminal::size().map(|(w, _)| w as usize).unwrap_or(80)
}

pub fn center_text(text: &str) -> String {
    let width = get_terminal_width();
    let text_len = strip_ansi(text).len();
    
    if text_len >= width {
        return text.to_string();
    }
    
    let left_padding = (width - text_len) / 2;
    format!("{}{}", " ".repeat(left_padding), text)
}

pub fn strip_ansi(text: &str) -> String {
    let re = regex::Regex::new(r"\x1B\[([0-9]{1,3}(;[0-9]{1,2})?)?[mGK]").unwrap();
    re.replace_all(text, "").to_string()
}

pub fn print_banner() {
    let width = get_terminal_width();
    let line = "=".repeat(width);
    
    let title1 = "XMU Rollcall Bot CLI";
    let title2 = "Version 3.1.0 (Rust Edition)";
    
    println!("{}{}{}", Colors::OKCYAN, line, Colors::ENDC);
    println!("{}", center_text(&format!("{}{}{}", Colors::BOLD, title1, Colors::ENDC)));
    println!("{}", center_text(&format!("{}{}{}", Colors::GRAY, title2, Colors::ENDC)));
    println!("{}{}{}", Colors::OKCYAN, line, Colors::ENDC);
}

pub fn print_separator(char: &str) {
    let width = get_terminal_width();
    println!("{}{}{}", Colors::GRAY, char.repeat(width), Colors::ENDC);
}

pub fn format_time(seconds: u64) -> String {
    let hours = seconds / 3600;
    let minutes = (seconds % 3600) / 60;
    let secs = seconds % 60;
    
    if hours > 0 {
        format!("{}h {}m {}s", hours, minutes, secs)
    } else if minutes > 0 {
        format!("{}m {}s", minutes, secs)
    } else {
        format!("{}s", secs)
    }
}

pub fn get_colorful_text(text: &str, color_offset: usize) -> String {
    let colors = [
        Colors::FAIL,
        Colors::WARNING,
        Colors::OKGREEN,
        Colors::OKCYAN,
        Colors::OKBLUE,
        Colors::HEADER,
    ];
    
    let mut result = String::new();
    for (i, ch) in text.chars().enumerate() {
        let color = colors[(i + color_offset) % colors.len()];
        result.push_str(color);
        result.push(ch);
    }
    result.push_str(Colors::ENDC);
    result
}

pub fn print_footer_text(color_offset: usize) {
    let text = "XMU-Rollcall-Bot @ KrsMt";
    let colored = get_colorful_text(text, color_offset);
    println!("{}", center_text(&colored));
}

pub fn print_dashboard(name: &str, start_time: std::time::Instant, query_count: u64) {
    crate::misc::clear_screen();
    print_banner();
    
    let local_time = chrono::Local::now().format("%Y-%m-%d %H:%M:%S").to_string();
    let greeting = crate::misc::get_greeting();
    let running_time = start_time.elapsed().as_secs();
    
    println!("\n{}{}{}, {}!{}\n", Colors::OKGREEN, Colors::BOLD, greeting, name, Colors::ENDC);
    
    println!("{}SYSTEM STATUS{}", Colors::BOLD, Colors::ENDC);
    print_separator("-");
    println!("{}Current Time:{}    {}{}{}", Colors::BOLD, Colors::ENDC, Colors::OKCYAN, local_time, Colors::ENDC);
    println!("{}Running Time:{}    {}{}{}", Colors::BOLD, Colors::ENDC, Colors::OKGREEN, format_time(running_time), Colors::ENDC);
    println!("{}Query Count:{}     {}{}{}", Colors::BOLD, Colors::ENDC, Colors::WARNING, query_count, Colors::ENDC);
    
    println!("\n{}ROLLCALL MONITOR{}", Colors::BOLD, Colors::ENDC);
    print_separator("-");
    println!("{}Status:{} Active - Monitoring for new rollcalls...", Colors::OKGREEN, Colors::ENDC);
    println!("{}Checking every 1 second(s){}", Colors::GRAY, Colors::ENDC);
    println!("{}Press Ctrl+C to exit{}\n", Colors::GRAY, Colors::ENDC);
    print_separator("-");
    
    println!();
    print_footer_text(0);
}

pub fn print_login_status(message: &str, is_success: bool) {
    if is_success {
        println!("{}[SUCCESS]{} {}", Colors::OKGREEN, Colors::ENDC, message);
    } else {
        println!("{}[FAILED]{} {}", Colors::FAIL, Colors::ENDC, message);
    }
}
