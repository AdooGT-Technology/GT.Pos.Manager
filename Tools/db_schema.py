TABLE_SCHEMAS = {
    "Hosts": """
        CREATE TABLE [Hosts] (
            HostId INT IDENTITY(1,1) PRIMARY KEY,
            HostName NVARCHAR(50) NOT NULL DEFAULT '',
            HostNumber INT NOT NULL DEFAULT 0,
            HostType NVARCHAR(20) DEFAULT 'PC',
            HostGroup NVARCHAR(50) DEFAULT 'أجهزة PC',
            IPAddress NVARCHAR(50) DEFAULT '',
            MACAddress NVARCHAR(50) DEFAULT '',
            Status NVARCHAR(20) DEFAULT 'متاح',
            CurrentUser NVARCHAR(100) DEFAULT '',
            CurrentSessionId INT NULL,
            IsActive BIT DEFAULT 1,
            CPU_Usage FLOAT DEFAULT 0,
            GPU_Usage FLOAT DEFAULT 0,
            RAM_Usage FLOAT DEFAULT 0,
            RAM_Total FLOAT DEFAULT 0,
            Disk_Usage FLOAT DEFAULT 0,
            CPU_Temp FLOAT DEFAULT 0,
            GPU_Temp FLOAT DEFAULT 0,
            GPU_Name NVARCHAR(200) DEFAULT '',
            VRAM_Used FLOAT DEFAULT 0,
            VRAM_Total FLOAT DEFAULT 0,
            RAM_Speed INT DEFAULT 0,
            Disk_Total FLOAT DEFAULT 0,
            Disk_Health NVARCHAR(20) DEFAULT '',
            Net_Name NVARCHAR(50) DEFAULT '',
            Net_Speed INT DEFAULT 0,
            Net_Upload FLOAT DEFAULT 0,
            Net_Download FLOAT DEFAULT 0,
            Net_Total FLOAT DEFAULT 0,
            UptimeMinutes INT DEFAULT 0,
            LastSeen DATETIME NULL,
            CreatedAt DATETIME DEFAULT GETDATE()
        )
    """,
    "Members": """
        CREATE TABLE [Members] (
            MemberId INT IDENTITY(1,1) PRIMARY KEY,
            Username NVARCHAR(50) NOT NULL UNIQUE,
            PasswordHash NVARCHAR(256) NOT NULL DEFAULT '',
            FullName NVARCHAR(100) DEFAULT '',
            Phone NVARCHAR(20) DEFAULT '',
            Email NVARCHAR(100) DEFAULT '',
            Balance DECIMAL(18,2) DEFAULT 0.00,
            Points INT DEFAULT 0,
            MemberType NVARCHAR(20) DEFAULT 'عادي',
            MemberGroup NVARCHAR(50) DEFAULT 'عادي',
            PurchasedMinutes INT DEFAULT 0,
            IsActive BIT DEFAULT 1,
            CreatedAt DATETIME DEFAULT GETDATE()
        )
    """,
    "Sessions": """
        CREATE TABLE [Sessions] (
            SessionId INT IDENTITY(1,1) PRIMARY KEY,
            HostId INT NOT NULL,
            MemberId INT NULL,
            GuestName NVARCHAR(100) DEFAULT 'ضيف',
            SessionType NVARCHAR(20) DEFAULT 'عادي',
            StartTime DATETIME DEFAULT GETDATE(),
            EndTime DATETIME NULL,
            Duration INT DEFAULT 0,
            Cost DECIMAL(18,2) DEFAULT 0.00,
            Status NVARCHAR(20) DEFAULT 'نشط',
            HostName NVARCHAR(50) DEFAULT '',
            MemberName NVARCHAR(100) DEFAULT '',
            HostGroup NVARCHAR(50) DEFAULT '',
            BillingProfile NVARCHAR(100) DEFAULT '',
            HourlyRate DECIMAL(18,2) DEFAULT 0.00,
            PaidMode NVARCHAR(20) DEFAULT 'deposit',
            MinutesPurchased INT DEFAULT 0,
            AmountCharged DECIMAL(18,2) DEFAULT 0.00,
            LastTick DATETIME NULL
        )
    """,
    "Shifts": """
        CREATE TABLE [Shifts] (
            ShiftId INT IDENTITY(1,1) PRIMARY KEY,
            StaffName NVARCHAR(100) DEFAULT '',
            OpenedAt DATETIME DEFAULT GETDATE(),
            ClosedAt DATETIME NULL,
            OpeningCash DECIMAL(18,2) DEFAULT 0.00,
            ExpectedCash DECIMAL(18,2) DEFAULT 0.00,
            ClosingCash DECIMAL(18,2) DEFAULT 0.00,
            Difference DECIMAL(18,2) DEFAULT 0.00,
            SalesCount INT DEFAULT 0,
            Status NVARCHAR(20) DEFAULT 'مفتوحة',
            Note NVARCHAR(300) DEFAULT ''
        )
    """,
    "CashMovements": """
        CREATE TABLE [CashMovements] (
            MovementId INT IDENTITY(1,1) PRIMARY KEY,
            ShiftId INT NULL,
            Kind NVARCHAR(10) DEFAULT 'in',
            Amount DECIMAL(18,2) DEFAULT 0.00,
            Reason NVARCHAR(200) DEFAULT '',
            CreatedBy NVARCHAR(80) DEFAULT '',
            CreatedAt DATETIME DEFAULT GETDATE()
        )
    """,
    "TransactionHistory": """
        CREATE TABLE [TransactionHistory] (
            TransId INT IDENTITY(1,1) PRIMARY KEY,
            MemberId INT NULL,
            HostId INT NULL,
            TransType NVARCHAR(50) NOT NULL DEFAULT '',
            Amount DECIMAL(18,2) DEFAULT 0.00,
            BalanceBefore DECIMAL(18,2) DEFAULT 0.00,
            BalanceAfter DECIMAL(18,2) DEFAULT 0.00,
            Description NVARCHAR(500) DEFAULT '',
            CreatedBy NVARCHAR(50) DEFAULT 'admin',
            CreatedAt DATETIME DEFAULT GETDATE()
        )
    """,
    "Orders": """
        CREATE TABLE [Orders] (
            OrderId INT IDENTITY(1,1) PRIMARY KEY,
            HostId INT NULL,
            MemberId INT NULL,
            ProductId INT NULL,
            ProductName NVARCHAR(100) DEFAULT '',
            Quantity INT DEFAULT 1,
            UnitPrice DECIMAL(18,2) DEFAULT 0.00,
            TotalPrice DECIMAL(18,2) DEFAULT 0.00,
            FinalAmount DECIMAL(18,2) DEFAULT 0.00,
            Status NVARCHAR(20) DEFAULT 'مكتمل',
            CreatedAt DATETIME DEFAULT GETDATE()
        )
    """,
    "Staff": """
        CREATE TABLE [Staff] (
            StaffId INT IDENTITY(1,1) PRIMARY KEY,
            Username NVARCHAR(50) NOT NULL UNIQUE,
            PasswordHash NVARCHAR(256) NOT NULL,
            FullName NVARCHAR(100) DEFAULT '',
            Role NVARCHAR(30) DEFAULT 'كاشير',
            Phone NVARCHAR(20) DEFAULT '',
            IsActive BIT DEFAULT 1,
            CreatedAt DATETIME DEFAULT GETDATE()
        )
    """,
    "Products": """
        CREATE TABLE [Products] (
            ProductId INT IDENTITY(1,1) PRIMARY KEY,
            ProductName NVARCHAR(100) NOT NULL,
            Category NVARCHAR(50) DEFAULT 'عام',
            Price DECIMAL(18,2) NOT NULL DEFAULT 0.00,
            Cost DECIMAL(18,2) DEFAULT 0.00,
            Stock INT DEFAULT 100,
            IconPath NVARCHAR(500) NULL,
            IsActive BIT DEFAULT 1,
            CreatedAt DATETIME DEFAULT GETDATE()
        )
    """,
    "Promotions": """
        CREATE TABLE [Promotions] (
            PromoId INT IDENTITY(1,1) PRIMARY KEY,
            PromoName NVARCHAR(100) NOT NULL,
            DiscountPercent FLOAT DEFAULT 0,
            StartDate DATETIME DEFAULT GETDATE(),
            EndDate DATETIME NULL,
            IsActive BIT DEFAULT 1
        )
    """,
        "Games": """
        CREATE TABLE [Games] (
            GameId INT IDENTITY(1,1) PRIMARY KEY,
            GameName NVARCHAR(200) NOT NULL,
            Category NVARCHAR(50) DEFAULT 'Other',
            Platform NVARCHAR(50) DEFAULT 'Standalone',
            GameType NVARCHAR(30) DEFAULT 'Offline Games',
            ExePath NVARCHAR(1000) DEFAULT '',
            IconPath NVARCHAR(500) NULL,
            TrailerUrl NVARCHAR(500) DEFAULT '',
            Description NVARCHAR(1000) DEFAULT '',
            AppId NVARCHAR(50) DEFAULT '',
            IsVisible BIT DEFAULT 1,
            IsInstalled BIT DEFAULT 1,
            SortOrder INT DEFAULT 0,
            CreatedAt DATETIME DEFAULT GETDATE()
        )
    """,
    "GameCategories": """
        CREATE TABLE [GameCategories] (
            CategoryId INT IDENTITY(1,1) PRIMARY KEY,
            CategoryName NVARCHAR(80) NOT NULL UNIQUE,
            IconEmoji NVARCHAR(10) DEFAULT '🎮',
            IsActive BIT DEFAULT 1,
            CreatedAt DATETIME DEFAULT GETDATE()
        )
    """,
    "Settings": """
        CREATE TABLE [Settings] (
            SettingId INT IDENTITY(1,1) PRIMARY KEY,
            SettingKey NVARCHAR(100) NOT NULL UNIQUE,
            SettingValue NVARCHAR(1000) DEFAULT '',
            SettingGroup NVARCHAR(50) DEFAULT 'general',
            CreatedAt DATETIME DEFAULT GETDATE()
        )
    """,
    "ActivityLog": """
        CREATE TABLE [ActivityLog] (
            LogId INT IDENTITY(1,1) PRIMARY KEY,
            LogType NVARCHAR(50) DEFAULT 'info',
            HostId INT NULL,
            MemberId INT NULL,
            UserName NVARCHAR(100) DEFAULT '',
            Description NVARCHAR(500) NOT NULL,
            Details NVARCHAR(1000) DEFAULT '',
            CreatedAt DATETIME DEFAULT GETDATE()
        )
    """
}

REQUIRED_COLUMNS = {
    "Hosts": {
        "HostName": "NVARCHAR(50) NOT NULL DEFAULT ''",
        "HostNumber": "INT NOT NULL DEFAULT 0",
        "HostType": "NVARCHAR(20) DEFAULT 'PC'",
        "IPAddress": "NVARCHAR(50) DEFAULT ''",
        "MACAddress": "NVARCHAR(50) DEFAULT ''",
        "Status": "NVARCHAR(20) DEFAULT 'متاح'",
        "CurrentUser": "NVARCHAR(100) DEFAULT ''",
        "CurrentSessionId": "INT NULL",
        "IsActive": "BIT DEFAULT 1",
        "CPU_Usage": "FLOAT DEFAULT 0",
        "GPU_Usage": "FLOAT DEFAULT 0",
        "RAM_Usage": "FLOAT DEFAULT 0",
        "RAM_Total": "FLOAT DEFAULT 0",
        "Disk_Usage": "FLOAT DEFAULT 0",
        "CPU_Temp": "FLOAT DEFAULT 0",
        "GPU_Temp": "FLOAT DEFAULT 0",
        "GPU_Name": "NVARCHAR(200) DEFAULT ''",
        "VRAM_Used": "FLOAT DEFAULT 0",
        "VRAM_Total": "FLOAT DEFAULT 0",
        "RAM_Speed": "INT DEFAULT 0",
        "Disk_Total": "FLOAT DEFAULT 0",
        "Disk_Health": "NVARCHAR(20) DEFAULT ''",
        "Net_Name": "NVARCHAR(50) DEFAULT ''",
        "Net_Speed": "INT DEFAULT 0",
        "Net_Upload": "FLOAT DEFAULT 0",
        "Net_Download": "FLOAT DEFAULT 0",
        "Net_Total": "FLOAT DEFAULT 0",
        "UptimeMinutes": "INT DEFAULT 0",
        "HostGroup": "NVARCHAR(50) DEFAULT 'أجهزة PC'",
        "LastSeen": "DATETIME NULL",
        "CreatedAt": "DATETIME DEFAULT GETDATE()"
    },
    "Sessions": {
        "HostId": "INT NOT NULL",
        "MemberId": "INT NULL",
        "GuestName": "NVARCHAR(100) DEFAULT 'ضيف'",
        "SessionType": "NVARCHAR(20) DEFAULT 'عادي'",
        "StartTime": "DATETIME DEFAULT GETDATE()",
        "EndTime": "DATETIME NULL",
        "Duration": "INT DEFAULT 0",
        "Cost": "DECIMAL(18,2) DEFAULT 0.00",
        "Status": "NVARCHAR(20) DEFAULT 'نشط'",
        "HostName": "NVARCHAR(50) DEFAULT ''",
        "MemberName": "NVARCHAR(100) DEFAULT ''",
        "HostGroup": "NVARCHAR(50) DEFAULT ''",
        "BillingProfile": "NVARCHAR(100) DEFAULT ''",
        "HourlyRate": "DECIMAL(18,2) DEFAULT 0.00",
        "PaidMode": "NVARCHAR(20) DEFAULT 'deposit'",
        "MinutesPurchased": "INT DEFAULT 0",
        "AmountCharged": "DECIMAL(18,2) DEFAULT 0.00",
        "LastTick": "DATETIME NULL"
    },
    "TransactionHistory": {
        "MemberId": "INT NULL",
        "HostId": "INT NULL",
        "TransType": "NVARCHAR(50) NOT NULL DEFAULT ''",
        "Amount": "DECIMAL(18,2) DEFAULT 0.00",
        "BalanceBefore": "DECIMAL(18,2) DEFAULT 0.00",
        "BalanceAfter": "DECIMAL(18,2) DEFAULT 0.00",
        "Description": "NVARCHAR(500) DEFAULT ''",
        "CreatedBy": "NVARCHAR(50) DEFAULT 'admin'",
        "CreatedAt": "DATETIME DEFAULT GETDATE()"
    },
    "Orders": {
        "HostId": "INT NULL",
        "MemberId": "INT NULL",
        "ProductId": "INT NULL",
        "ProductName": "NVARCHAR(100) DEFAULT ''",
        "Quantity": "INT DEFAULT 1",
        "UnitPrice": "DECIMAL(18,2) DEFAULT 0.00",
        "TotalPrice": "DECIMAL(18,2) DEFAULT 0.00",
        "FinalAmount": "DECIMAL(18,2) DEFAULT 0.00",
        "Status": "NVARCHAR(20) DEFAULT 'مكتمل'",
        "CreatedAt": "DATETIME DEFAULT GETDATE()"
    },
    "Members": {
        "Username": "NVARCHAR(50) NOT NULL",
        "PasswordHash": "NVARCHAR(256) NOT NULL DEFAULT ''",
        "FullName": "NVARCHAR(100) DEFAULT ''",
        "Phone": "NVARCHAR(20) DEFAULT ''",
        "Email": "NVARCHAR(100) DEFAULT ''",
        "Balance": "DECIMAL(18,2) DEFAULT 0.00",
        "Points": "INT DEFAULT 0",
        "MemberType": "NVARCHAR(20) DEFAULT 'عادي'",
        "MemberGroup": "NVARCHAR(50) DEFAULT 'عادي'",
        "PurchasedMinutes": "INT DEFAULT 0",
        "IsActive": "BIT DEFAULT 1",
        "CreatedAt": "DATETIME DEFAULT GETDATE()"
    },
    "Staff": {
        "Username": "NVARCHAR(50) NOT NULL",
        "PasswordHash": "NVARCHAR(256) NOT NULL",
        "FullName": "NVARCHAR(100) DEFAULT ''",
        "Role": "NVARCHAR(30) DEFAULT 'كاشير'",
        "Phone": "NVARCHAR(20) DEFAULT ''",
        "IsActive": "BIT DEFAULT 1",
        "CreatedAt": "DATETIME DEFAULT GETDATE()"
    },
    "Products": {
        "ProductName": "NVARCHAR(100) NOT NULL",
        "Category": "NVARCHAR(50) DEFAULT 'عام'",
        "Price": "DECIMAL(18,2) NOT NULL DEFAULT 0.00",
        "Cost": "DECIMAL(18,2) DEFAULT 0.00",
        "Stock": "INT DEFAULT 100",
        "IconPath": "NVARCHAR(500) NULL",
        "IsActive": "BIT DEFAULT 1",
        "CreatedAt": "DATETIME DEFAULT GETDATE()"
    },
    "Promotions": {
        "PromoName": "NVARCHAR(100) NOT NULL",
        "DiscountPercent": "FLOAT DEFAULT 0",
        "StartDate": "DATETIME DEFAULT GETDATE()",
        "EndDate": "DATETIME NULL",
        "IsActive": "BIT DEFAULT 1"
    },
    "Games": {
        "GameName": "NVARCHAR(200) NOT NULL",
        "Category": "NVARCHAR(50) DEFAULT 'Other'",
        "Platform": "NVARCHAR(50) DEFAULT 'Standalone'",
        "GameType": "NVARCHAR(30) DEFAULT 'Offline Games'",
        "ExePath": "NVARCHAR(1000) DEFAULT ''",
        "IconPath": "NVARCHAR(500) NULL",
        "AppId": "NVARCHAR(50) DEFAULT ''",
        "IsVisible": "BIT DEFAULT 1",
        "IsInstalled": "BIT DEFAULT 1",
        "SortOrder": "INT DEFAULT 0",
        "TrailerUrl": "NVARCHAR(500) DEFAULT ''",
        "Description": "NVARCHAR(1000) DEFAULT ''",
        "CreatedAt": "DATETIME DEFAULT GETDATE()"
        
    },
    "GameCategories": {
        "CategoryName": "NVARCHAR(80) NOT NULL",
        "IconEmoji": "NVARCHAR(10) DEFAULT '🎮'",
        "IsActive": "BIT DEFAULT 1",
        "CreatedAt": "DATETIME DEFAULT GETDATE()"
    },
    "Settings": {
        "SettingKey": "NVARCHAR(100) NOT NULL",
        "SettingValue": "NVARCHAR(1000) DEFAULT ''",
        "SettingGroup": "NVARCHAR(50) DEFAULT 'general'",
        "CreatedAt": "DATETIME DEFAULT GETDATE()"
    },
    "ActivityLog": {
        "LogType": "NVARCHAR(50) DEFAULT 'info'",
        "HostId": "INT NULL",
        "MemberId": "INT NULL",
        "UserName": "NVARCHAR(100) DEFAULT ''",
        "Description": "NVARCHAR(500) NOT NULL",
        "Details": "NVARCHAR(1000) DEFAULT ''",
        "CreatedAt": "DATETIME DEFAULT GETDATE()"
    }
}

STORED_PROCEDURES = {
    "sp_StartSession": """
        CREATE OR ALTER PROCEDURE sp_StartSession
            @HostId INT, @MemberId INT = NULL, @GuestName NVARCHAR(100) = 'ضيف'
        AS BEGIN
            DECLARE @SessionId INT;
            INSERT INTO Sessions (HostId, MemberId, GuestName, StartTime, Status)
            VALUES (@HostId, @MemberId, @GuestName, GETDATE(), N'نشط');
            SET @SessionId = SCOPE_IDENTITY();
            DECLARE @UserName NVARCHAR(100) = ISNULL((SELECT Username FROM Members WHERE MemberId=@MemberId), @GuestName);
            UPDATE Hosts SET Status=N'مشغول', CurrentUser=@UserName, CurrentSessionId=@SessionId WHERE HostId=@HostId;
            INSERT INTO ActivityLog (LogType, HostId, MemberId, UserName, Description)
            VALUES ('login', @HostId, @MemberId, @UserName, N'تم تسجيل دخول المستخدم ' + @UserName);
            SELECT @SessionId AS SessionId;
        END
    """,
    "sp_EndSession": """
        CREATE OR ALTER PROCEDURE sp_EndSession @HostId INT
        AS BEGIN
            DECLARE @SessionId INT, @StartTime DATETIME, @Duration INT, @Cost DECIMAL(18,2);
            DECLARE @UserName NVARCHAR(100);
            SELECT @SessionId=SessionId, @StartTime=StartTime FROM Sessions
            WHERE HostId=@HostId AND Status=N'نشط' ORDER BY StartTime DESC;
            IF @SessionId IS NOT NULL BEGIN
                SET @Duration = DATEDIFF(SECOND, @StartTime, GETDATE());
                SET @Cost = ROUND(@Duration / 3600.0 * 20, 2);
                SELECT @UserName = CurrentUser FROM Hosts WHERE HostId = @HostId;
                UPDATE Sessions SET EndTime=GETDATE(), Duration=@Duration, Cost=@Cost, Status=N'منتهية' WHERE SessionId=@SessionId;
                UPDATE Hosts SET Status=N'متاح', CurrentUser='', CurrentSessionId=NULL WHERE HostId=@HostId;
                INSERT INTO ActivityLog (LogType, HostId, UserName, Description)
                VALUES ('logout', @HostId, @UserName, N'تم تسجيل خروج المستخدم ' + ISNULL(@UserName, ''));
            END
        END
    """,
    "sp_AddBalance": """
        CREATE OR ALTER PROCEDURE sp_AddBalance
            @MemberId INT, @Amount DECIMAL(18,2), @CreatedBy NVARCHAR(50) = 'admin'
        AS BEGIN
            DECLARE @Before DECIMAL(18,2), @UserName NVARCHAR(100);
            SELECT @Before=Balance, @UserName=Username FROM Members WHERE MemberId=@MemberId;
            UPDATE Members SET Balance=Balance+@Amount WHERE MemberId=@MemberId;
            INSERT INTO TransactionHistory (MemberId, TransType, Amount, BalanceBefore, BalanceAfter, Description, CreatedBy)
            VALUES (@MemberId, N'إيداع', @Amount, @Before, @Before+@Amount, N'إضافة رصيد', @CreatedBy);
            INSERT INTO ActivityLog (LogType, MemberId, UserName, Description, Details)
            VALUES ('deposit', @MemberId, @UserName, N'تم إضافة رصيد للمحفظة', N'المبلغ: $' + CAST(@Amount AS NVARCHAR) + N' - المستخدم ' + ISNULL(@UserName,''));
        END
    """,
    "sp_DailySalesReport": """
        CREATE OR ALTER PROCEDURE sp_DailySalesReport
        AS BEGIN
            SELECT
                COUNT(DISTINCT SessionId) AS TotalSessions,
                ISNULL(SUM(Cost), 0) AS TotalRevenue,
                ISNULL(SUM(Duration)/3600.0, 0) AS TotalHours
            FROM Sessions
            WHERE CAST(StartTime AS DATE) = CAST(GETDATE() AS DATE);
        END
    """
}

def _settings_seed():
    """Insert the settings catalogue blobs so a fresh database opens fully configured."""
    import json
    from Manager.settings_schema import sections

    statements = []
    for _group, section in sections():
        blob = json.dumps(section.get("defaults") or {}, ensure_ascii=False).replace("'", "''")
        key = f"settings.{section['key']}"
        statements.append(
            "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey=N'%s') "
            "INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) "
            "VALUES (N'%s', N'%s', 'settings')" % (key, key, blob)
        )
    return statements


def _billing_seed():
    """Gizmo-style billing catalogue: user groups, host groups, profiles, offers."""
    import json

    catalogs = {
        "settings.billing.usergroups": {
            "rows": [
                {"name": "زائر", "kind": "guest", "profile": "التسعير الأساسي", "discount": 0, "points": 1, "active": True},
                {"name": "عادي", "kind": "member", "profile": "التسعير الأساسي", "discount": 0, "points": 1, "active": True},
                {"name": "VIP", "kind": "member", "profile": "تسعير VIP", "discount": 15, "points": 2, "active": True},
                {"name": "eSports", "kind": "member", "profile": "تسعير البطولات", "discount": 10, "points": 2, "active": True},
            ]
        },
        "settings.billing.hostgroups": {
            "rows": [
                {"name": "أجهزة PC", "profile": "", "note": "السعر الافتراضي لمجموعة العضو"},
                {"name": "غرف VIP", "profile": "تسعير VIP", "note": "سعر أعلى للأجهزة المميزة"},
                {"name": "بلايستيشن", "profile": "تسعير الكونسول", "note": "أجهزة كونسول"},
            ]
        },
        "settings.billing.profiles": {
            "rows": [
                {"name": "التسعير الأساسي", "hourly": 15, "minimum": 30, "round": 15, "active": True,
                 "custom": "18:00-23:00=20;23:00-06:00=12"},
                {"name": "تسعير VIP", "hourly": 25, "minimum": 60, "round": 15, "active": True,
                 "custom": "18:00-23:00=30"},
                {"name": "تسعير الكونسول", "hourly": 20, "minimum": 30, "round": 15, "active": True,
                 "custom": ""},
                {"name": "تسعير البطولات", "hourly": 35, "minimum": 60, "round": 30, "active": True,
                 "custom": "18:00-23:00=40"},
            ]
        },
        "settings.billing.offers": {
            "rows": [
                {"name": "عرض الساعة الذهبية", "minutes": 60, "price": 12, "from": "14:00", "to": "17:00", "active": True},
                {"name": "باقة 3 ساعات", "minutes": 180, "price": 35, "from": "", "to": "", "active": True},
                {"name": "ليلة كاملة", "minutes": 300, "price": 50, "from": "23:00", "to": "05:00", "active": True},
                {"name": "عرض نهاية الأسبوع", "minutes": 240, "price": 45, "from": "", "to": "", "active": False},
            ]
        },
    }
    statements = []
    for key, payload in catalogs.items():
        blob = json.dumps(payload, ensure_ascii=False).replace("'", "''")
        statements.append(
            "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey=N'%s') "
            "INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) "
            "VALUES (N'%s', N'%s', 'billing')" % (key, key, blob)
        )
    return statements


DEFAULT_DATA = {
    "Staff": [
        "IF NOT EXISTS (SELECT 1 FROM Staff WHERE Username='admin') INSERT INTO Staff (Username, PasswordHash, FullName, Role, IsActive) VALUES ('admin', 'admin123', N'مدير النظام', N'مدير', 1) ELSE UPDATE Staff SET PasswordHash='admin123', IsActive=1 WHERE Username='admin'"
    ],
    "Hosts": [
        f"IF NOT EXISTS (SELECT 1 FROM Hosts WHERE HostNumber={i}) INSERT INTO Hosts (HostName, HostNumber, HostType, IPAddress, Status) VALUES (N'PC-{i:02d}', {i}, 'PC', '192.168.1.{100+i}', N'متاح')"
        for i in range(1, 9)
    ],
    "Products": [
        "IF NOT EXISTS (SELECT 1 FROM Products WHERE ProductName=N'بيبسي 330 مل') INSERT INTO Products (ProductName, Category, Price, Cost, Stock) VALUES (N'بيبسي 330 مل', N'مشروبات', 15.00, 8.00, 100)",
        "IF NOT EXISTS (SELECT 1 FROM Products WHERE ProductName=N'مشروب طاقة') INSERT INTO Products (ProductName, Category, Price, Cost, Stock) VALUES (N'مشروب طاقة', N'مشروبات', 45.00, 30.00, 50)",
        "IF NOT EXISTS (SELECT 1 FROM Products WHERE ProductName=N'ساندويتش برجر') INSERT INTO Products (ProductName, Category, Price, Cost, Stock) VALUES (N'ساندويتش برجر', N'وجبات', 65.00, 35.00, 30)",
        "IF NOT EXISTS (SELECT 1 FROM Products WHERE ProductName=N'بطاطس مقلية') INSERT INTO Products (ProductName, Category, Price, Cost, Stock) VALUES (N'بطاطس مقلية', N'وجبات', 30.00, 15.00, 40)",
        "IF NOT EXISTS (SELECT 1 FROM Products WHERE ProductName=N'قهوة اسبريسو') INSERT INTO Products (ProductName, Category, Price, Cost, Stock) VALUES (N'قهوة اسبريسو', N'مشروبات ساخنة', 25.00, 10.00, 80)"
    ],
    "Games": [
        "IF NOT EXISTS (SELECT 1 FROM Games WHERE GameName=N'Counter-Strike 2') INSERT INTO Games (GameName, Category, Platform, GameType, AppId, SortOrder) VALUES (N'Counter-Strike 2', 'FPS', 'Steam', 'Online Games', '730', 1)",
        "IF NOT EXISTS (SELECT 1 FROM Games WHERE GameName=N'Valorant') INSERT INTO Games (GameName, Category, Platform, GameType, AppId, SortOrder) VALUES (N'Valorant', 'FPS', 'Riot Games', 'Online Games', '', 2)",
        "IF NOT EXISTS (SELECT 1 FROM Games WHERE GameName=N'League of Legends') INSERT INTO Games (GameName, Category, Platform, GameType, AppId, SortOrder) VALUES (N'League of Legends', 'MOBA', 'Riot Games', 'Online Games', '', 3)",
        "IF NOT EXISTS (SELECT 1 FROM Games WHERE GameName=N'Fortnite') INSERT INTO Games (GameName, Category, Platform, GameType, AppId, SortOrder) VALUES (N'Fortnite', 'Battle Royale', 'Epic Games', 'Online Games', '', 4)",
        "IF NOT EXISTS (SELECT 1 FROM Games WHERE GameName=N'Apex Legends') INSERT INTO Games (GameName, Category, Platform, GameType, AppId, SortOrder) VALUES (N'Apex Legends', 'Battle Royale', 'EA', 'Online Games', '', 5)",
        "IF NOT EXISTS (SELECT 1 FROM Games WHERE GameName=N'GTA V') INSERT INTO Games (GameName, Category, Platform, GameType, AppId, SortOrder) VALUES (N'GTA V', 'Action', 'Steam', 'Offline Games', '271590', 6)",
        "IF NOT EXISTS (SELECT 1 FROM Games WHERE GameName=N'FIFA 24') INSERT INTO Games (GameName, Category, Platform, GameType, AppId, SortOrder) VALUES (N'FIFA 24', 'Sports', 'EA App', 'Offline Games', '', 7)",
        "IF NOT EXISTS (SELECT 1 FROM Games WHERE GameName=N'Minecraft') INSERT INTO Games (GameName, Category, Platform, GameType, AppId, SortOrder) VALUES (N'Minecraft', 'Sandbox', 'Standalone', 'Offline Games', '', 8)",
        "IF NOT EXISTS (SELECT 1 FROM Games WHERE GameName=N'PUBG') INSERT INTO Games (GameName, Category, Platform, GameType, AppId, SortOrder) VALUES (N'PUBG', 'Battle Royale', 'Steam', 'Online Games', '578080', 9)",
        "IF NOT EXISTS (SELECT 1 FROM Games WHERE GameName=N'Overwatch 2') INSERT INTO Games (GameName, Category, Platform, GameType, AppId, SortOrder) VALUES (N'Overwatch 2', 'FPS', 'Battle.net', 'Online Games', '', 10)",
        "IF NOT EXISTS (SELECT 1 FROM Games WHERE GameName=N'Rocket League') INSERT INTO Games (GameName, Category, Platform, GameType, AppId, SortOrder) VALUES (N'Rocket League', 'Sports', 'Epic Games', 'Online Games', '', 11)",
        "IF NOT EXISTS (SELECT 1 FROM Games WHERE GameName=N'Dota 2') INSERT INTO Games (GameName, Category, Platform, GameType, AppId, SortOrder) VALUES (N'Dota 2', 'MOBA', 'Steam', 'Online Games', '570', 12)",
        "IF NOT EXISTS (SELECT 1 FROM Games WHERE GameName=N'Call of Duty MW') INSERT INTO Games (GameName, Category, Platform, GameType, AppId, SortOrder) VALUES (N'Call of Duty MW', 'FPS', 'Battle.net', 'Online Games', '', 13)",
        "IF NOT EXISTS (SELECT 1 FROM Games WHERE GameName=N'Assassins Creed') INSERT INTO Games (GameName, Category, Platform, GameType, AppId, SortOrder) VALUES (N'Assassins Creed', 'Action', 'Steam', 'Offline Games', '15100', 14)",
        "IF NOT EXISTS (SELECT 1 FROM Games WHERE GameName=N'Battlefield 6') INSERT INTO Games (GameName, Category, Platform, GameType, AppId, SortOrder) VALUES (N'Battlefield 6', 'FPS', 'EA', 'Online Games', '', 15)",
        "IF NOT EXISTS (SELECT 1 FROM Games WHERE GameName=N'CrossFire') INSERT INTO Games (GameName, Category, Platform, GameType, AppId, SortOrder) VALUES (N'CrossFire', 'FPS', 'Standalone', 'Online Games', '', 16)",
        "IF NOT EXISTS (SELECT 1 FROM Games WHERE GameName=N'Roblox') INSERT INTO Games (GameName, Category, Platform, GameType, AppId, SortOrder) VALUES (N'Roblox', 'Sandbox', 'Standalone', 'Online Games', '', 17)",
        "IF NOT EXISTS (SELECT 1 FROM Games WHERE GameName=N'Among Us') INSERT INTO Games (GameName, Category, Platform, GameType, AppId, SortOrder) VALUES (N'Among Us', 'Party', 'Steam', 'Online Games', '945360', 18)"
    ],
    "GameCategories": [
        "IF NOT EXISTS (SELECT 1 FROM GameCategories WHERE CategoryName='FPS') INSERT INTO GameCategories (CategoryName, IconEmoji) VALUES ('FPS', '🔫')",
        "IF NOT EXISTS (SELECT 1 FROM GameCategories WHERE CategoryName='MOBA') INSERT INTO GameCategories (CategoryName, IconEmoji) VALUES ('MOBA', '⚔️')",
        "IF NOT EXISTS (SELECT 1 FROM GameCategories WHERE CategoryName='Battle Royale') INSERT INTO GameCategories (CategoryName, IconEmoji) VALUES ('Battle Royale', '🪂')",
        "IF NOT EXISTS (SELECT 1 FROM GameCategories WHERE CategoryName='Action') INSERT INTO GameCategories (CategoryName, IconEmoji) VALUES ('Action', '💥')",
        "IF NOT EXISTS (SELECT 1 FROM GameCategories WHERE CategoryName='Sports') INSERT INTO GameCategories (CategoryName, IconEmoji) VALUES ('Sports', '⚽')",
        "IF NOT EXISTS (SELECT 1 FROM GameCategories WHERE CategoryName='Racing') INSERT INTO GameCategories (CategoryName, IconEmoji) VALUES ('Racing', '🏎️')",
        "IF NOT EXISTS (SELECT 1 FROM GameCategories WHERE CategoryName='Sandbox') INSERT INTO GameCategories (CategoryName, IconEmoji) VALUES ('Sandbox', '🧱')",
        "IF NOT EXISTS (SELECT 1 FROM GameCategories WHERE CategoryName='RPG') INSERT INTO GameCategories (CategoryName, IconEmoji) VALUES ('RPG', '🗡️')",
        "IF NOT EXISTS (SELECT 1 FROM GameCategories WHERE CategoryName='Strategy') INSERT INTO GameCategories (CategoryName, IconEmoji) VALUES ('Strategy', '♟️')",
        "IF NOT EXISTS (SELECT 1 FROM GameCategories WHERE CategoryName='Party') INSERT INTO GameCategories (CategoryName, IconEmoji) VALUES ('Party', '🎉')",
        "IF NOT EXISTS (SELECT 1 FROM GameCategories WHERE CategoryName='Other') INSERT INTO GameCategories (CategoryName, IconEmoji) VALUES ('Other', '🎮')"
    ],
    "Settings": _settings_seed() + _billing_seed() + [
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='center_name') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('center_name', N'Gaming Center Pro', 'general')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='center_description') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('center_description', N'أحدث أجهزة الكمبيوتر - أسرع إنترنت - أفضل تجربة ألعاب', 'general')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='currency') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('currency', N'جنيه مصري (EGP)', 'financial')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='hourly_rate') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('hourly_rate', '20', 'financial')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='min_deposit') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('min_deposit', '50', 'financial')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='service_fee') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('service_fee', '5', 'financial')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='tax_enabled') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('tax_enabled', '0', 'financial')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='default_payment') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('default_payment', N'محفظة إلكترونية', 'financial')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='device_count') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('device_count', '12', 'devices')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='default_session_time') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('default_session_time', '1:00:00', 'devices')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='auto_restart') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('auto_restart', '0', 'devices')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='shutdown_after_session') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('shutdown_after_session', '0', 'devices')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='center_open') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('center_open', '1', 'general')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='connection_type') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('connection_type', 'DHCP', 'network')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='internet_speed') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('internet_speed', '100', 'network')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='dns_settings') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('dns_settings', '8.8.8.8 , 8.8.4.4', 'network')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='speed_monitor') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('speed_monitor', '1', 'network')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='max_members') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('max_members', '100', 'accounts')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='auto_login') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('auto_login', '0', 'accounts')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='two_factor') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('two_factor', '0', 'accounts')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='log_activity') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('log_activity', '1', 'accounts')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='lock_after_fails') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('lock_after_fails', '5', 'accounts')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='enable_invoices') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('enable_invoices', '1', 'sales')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='print_receipt') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('print_receipt', '1', 'sales')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='invoice_format') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('invoice_format', N'فاتورة احترافية', 'sales')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='vat_enabled') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('vat_enabled', '0', 'sales')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='invoice_prefix') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('invoice_prefix', 'INV-2025-0001', 'sales')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='min_withdraw') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('min_withdraw', '50', 'sales')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='rewards_enabled') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('rewards_enabled', '0', 'rewards')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='points_per_hour') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('points_per_hour', '50', 'rewards')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='max_points') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('max_points', '10000', 'rewards')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='points_validity_days') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('points_validity_days', '30', 'rewards')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='special_offers') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('special_offers', '1', 'rewards')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='esports_enabled') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('esports_enabled', '0', 'esports')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='max_teams') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('max_teams', '12', 'esports')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='match_system') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('match_system', N'افتراضي', 'esports')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='live_stream') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('live_stream', '0', 'esports')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='esports_rewards') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('esports_rewards', '1', 'esports')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='system_notifications') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('system_notifications', '1', 'notifications')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='user_notifications') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('user_notifications', '1', 'notifications')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='sales_notifications') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('sales_notifications', '1', 'notifications')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='rewards_notifications') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('rewards_notifications', '0', 'rewards')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='email_notifications') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('email_notifications', '0', 'notifications')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='sms_notifications') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('sms_notifications', '0', 'notifications')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='auto_lock_minutes') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('auto_lock_minutes', '15', 'security')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='encryption_enabled') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('encryption_enabled', '0', 'security')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='auto_backup') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('auto_backup', '0', 'security')",
        "IF NOT EXISTS (SELECT 1 FROM Settings WHERE SettingKey='login_log') INSERT INTO Settings (SettingKey, SettingValue, SettingGroup) VALUES ('login_log', '1', 'security')"
    ]
}