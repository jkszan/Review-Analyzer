CREATE TABLE IF NOT EXISTS employer (
    companyName VARCHAR(30) PRIMARY KEY,
    url VARCHAR(200)
);

CREATE TABLE IF NOT EXISTS review (
    review_id VARCHAR(50),
    company VARCHAR(100) REFERENCES employer(companyName),
    rating float NOT NULL,
    headline LONGTEXT,
    location VARCHAR(100),
    employeestatus VARCHAR(50),
    jobtitle VARCHAR(100),
    dateposted date NOT NULL,
    pros LONGTEXT,
    cons LONGTEXT,
    PRIMARY KEY (review_id, company)
);