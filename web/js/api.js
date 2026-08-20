const BASE_URL = window.location.port === '5173' ? `http://${window.location.hostname}:8000` : window.location.origin;

/**
 * Fetch consolidated dashboard summary for a region and year.
 * @param {string} region - Region key (e.g. '서울특별시|양천구')
 * @param {number} year - Target year (e.g. 2024)
 */
async function fetchSummary(region, year) {
    const response = await fetch(`${BASE_URL}/api/summary?region=${encodeURIComponent(region)}&year=${year}`);
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `API error: ${response.statusText}`);
    }
    return await response.json();
}

/**
 * Fetch prioritized segments filterable by region.
 * @param {string|null} region - Optional region key
 * @param {number} year - Target year
 */
async function fetchPriority(region, year) {
    let url = `${BASE_URL}/api/priority?year=${year}`;
    if (region) {
        url += `&region=${encodeURIComponent(region)}`;
    }
    const response = await fetch(url);
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `API error: ${response.statusText}`);
    }
    return await response.json();
}

/**
 * Fetch comparison data for a specific segment against its 20 similar regions.
 * @param {string} region - Region key
 * @param {string} gender - '남자' or '여자'
 * @param {string} age - Age group (e.g. '65~69')
 * @param {string} cancer - Cancer type (e.g. '대장암')
 * @param {number} year - Target year
 */
async function fetchCompare(region, gender, age, cancer, year) {
    const params = new URLSearchParams({
        region,
        gender,
        age,
        cancer,
        year
    });
    const response = await fetch(`${BASE_URL}/api/compare?${params.toString()}`);
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `API error: ${response.statusText}`);
    }
    return await response.json();
}

/**
 * Fetch factor analysis (contribution to screening rate) for a specific segment.
 * @param {string} region - Region key
 * @param {string} sex - '남자' or '여자'
 * @param {string} age - Age group (e.g. '65~69')
 * @param {string} cancer - Cancer type (e.g. '대장암')
 * @param {number} year - Target year
 */
async function fetchFactors(region, sex, age, cancer, year) {
    const params = new URLSearchParams({
        region,
        sex,
        age,
        cancer,
        year
    });
    const response = await fetch(`${BASE_URL}/api/factors?${params.toString()}`);
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `API error: ${response.statusText}`);
    }
    return await response.json();
}

/**
 * Fetch intervention strategies and survey questions for a segment.
 * @param {string} region - Region key
 * @param {string} sex - '남자' or '여자'
 * @param {string} age - Age group
 * @param {string} cancer - Cancer type
 * @param {number} year - Target year
 */
async function fetchActions(region, sex, age, cancer, year) {
    const params = new URLSearchParams({
        region,
        sex,
        age,
        cancer,
        year
    });
    const response = await fetch(`${BASE_URL}/api/actions?${params.toString()}`);
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `API error: ${response.statusText}`);
    }
    return await response.json();
}

/**
 * Request randomized sample splitting for a target segment.
 * @param {string} region - Region key
 * @param {string} sex - '남자' or '여자'
 * @param {string} age - Age group
 * @param {string} cancer - Cancer type
 * @param {number} n - Target contact size
 * @param {number} seed - Random seed
 */
async function postSample(region, sex, age, cancer, n, seed) {
    const payload = {
        region,
        sex,
        age,
        cancer,
        n: parseInt(n),
        seed: parseInt(seed)
    };
    const response = await fetch(`${BASE_URL}/api/sample`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `API error: ${response.statusText}`);
    }
    return await response.json();
}

/**
 * Fetch campaign records for a region and year.
 * @param {string} region - Region key
 * @param {number} year - Target year
 */
async function fetchRecords(region, year) {
    const params = new URLSearchParams({ region, year });
    const response = await fetch(`${BASE_URL}/api/records?${params.toString()}`);
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `API error: ${response.statusText}`);
    }
    return await response.json();
}

/**
 * Update campaign execution results.
 * @param {object} payload - CampaignRecordUpdateRequest structure
 */
async function updateRecord(payload) {
    const response = await fetch(`${BASE_URL}/api/records`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `API error: ${response.statusText}`);
    }
    return await response.json();
}

/**
 * Generate guidance text with LLM.
 * @param {object} payload - MessageRequest structure
 */
async function postMessageGeneration(payload) {
    const response = await fetch(`${BASE_URL}/api/message`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `API error: ${response.statusText}`);
    }
    return await response.json();
}

/**
 * Generate report text with LLM.
 * @param {object} payload - ReportRequest structure
 */
async function postReportGeneration(payload) {
    const response = await fetch(`${BASE_URL}/api/report`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `API error: ${response.statusText}`);
    }
    return await response.json();
}

/**
 * Request chatbot guidance response from Onco.
 * @param {object} payload - ChatRequest structure
 */
async function postChat(payload) {
    const response = await fetch(`${BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `API error: ${response.statusText}`);
    }
    return await response.json();
}

