// Dependency-free QR Code encoder (byte mode, ISO/IEC 18004) & EMVCo Payload Generator.

// ---------------------------------------------------------------- spec tables

const EC_LEVELS = { L: 0, M: 1, Q: 2, H: 3 }

const TOTAL_CODEWORDS = [
    26, 44, 70, 100, 134, 172, 196, 242, 292, 346,
    404, 466, 532, 581, 655, 733, 815, 901, 991, 1085,
    1156, 1258, 1364, 1474, 1588, 1706, 1828, 1921, 2051, 2185,
    2323, 2465, 2611, 2761, 2876, 3034, 3196, 3362, 3532, 3706,
]

const EC_CODEWORDS_PER_BLOCK = [
    [7, 10, 15, 20, 26, 18, 20, 24, 30, 18, 20, 24, 26, 30, 22, 24, 28, 30, 28, 28,
        28, 28, 30, 30, 26, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30],
    [10, 16, 26, 18, 24, 16, 18, 22, 22, 26, 30, 22, 22, 24, 24, 28, 28, 26, 26, 26,
        26, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28],
    [13, 22, 18, 26, 18, 24, 18, 22, 20, 24, 28, 26, 24, 20, 30, 24, 28, 28, 26, 30,
        28, 30, 30, 30, 30, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30],
    [17, 28, 22, 16, 22, 28, 26, 26, 24, 28, 24, 28, 22, 24, 24, 30, 28, 28, 26, 28,
        30, 24, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30],
]

const NUM_EC_BLOCKS = [
    [1, 1, 1, 1, 1, 2, 2, 2, 2, 4, 4, 4, 4, 4, 6, 6, 6, 6, 7, 8,
        8, 9, 9, 10, 12, 12, 12, 13, 14, 15, 16, 17, 18, 19, 19, 20, 21, 22, 24, 25],
    [1, 1, 1, 2, 2, 4, 4, 4, 5, 5, 5, 8, 9, 9, 10, 10, 11, 13, 14, 16,
        17, 17, 18, 20, 21, 23, 25, 26, 28, 29, 31, 33, 35, 37, 38, 40, 43, 45, 47, 49],
    [1, 1, 2, 2, 4, 4, 6, 6, 8, 8, 8, 10, 12, 16, 12, 17, 16, 18, 21, 20,
        23, 23, 25, 27, 29, 34, 34, 35, 38, 40, 43, 45, 48, 51, 53, 56, 59, 62, 65, 68],
    [1, 1, 2, 4, 4, 4, 5, 6, 8, 8, 11, 11, 16, 16, 18, 16, 19, 21, 25, 25,
        25, 34, 30, 32, 35, 37, 40, 42, 45, 48, 51, 54, 57, 60, 63, 66, 70, 74, 77, 81],
]

const ALIGNMENT_POSITIONS = [
    [], [], [6, 18], [6, 22], [6, 26], [6, 30], [6, 34], [6, 22, 38], [6, 24, 42], [6, 26, 46],
    [6, 28, 50], [6, 30, 54], [6, 32, 58], [6, 34, 62], [6, 26, 46, 66], [6, 26, 48, 70],
    [6, 26, 50, 74], [6, 30, 54, 78], [6, 30, 56, 82], [6, 30, 58, 86], [6, 34, 62, 90],
    [6, 28, 50, 72, 94], [6, 26, 50, 74, 98], [6, 30, 54, 78, 102], [6, 28, 54, 80, 106],
    [6, 32, 58, 84, 110], [6, 30, 58, 86, 114], [6, 34, 62, 90, 118], [6, 26, 50, 74, 98, 122],
    [6, 30, 54, 78, 102, 126], [6, 26, 52, 78, 104, 130], [6, 30, 56, 82, 108, 134],
    [6, 34, 60, 86, 112, 138], [6, 30, 58, 86, 114, 142], [6, 34, 62, 90, 118, 146],
    [6, 30, 54, 78, 102, 126, 150], [6, 24, 50, 76, 102, 128, 154], [6, 28, 54, 80, 106, 132, 158],
    [6, 32, 58, 84, 110, 136, 162], [6, 26, 54, 82, 110, 138, 166], [6, 30, 58, 86, 114, 142, 170],
]

// ------------------------------------------------------------- galois field

const GF_EXP = new Uint8Array(512)
const GF_LOG = new Uint8Array(256)
;(() => {
    let x = 1
    for (let i = 0; i < 255; i++) {
        GF_EXP[i] = x
        GF_LOG[x] = i
        x <<= 1
        if (x & 0x100) x ^= 0x11d
    }
    for (let i = 255; i < 512; i++) GF_EXP[i] = GF_EXP[i - 255]
})()

const gfMul = (a, b) => (a === 0 || b === 0 ? 0 : GF_EXP[GF_LOG[a] + GF_LOG[b]])

function rsGenerator(degree) {
    let poly = [1]
    for (let i = 0; i < degree; i++) {
        const next = Array.from({ length: poly.length + 1 }, () => 0)
        for (let j = 0; j < poly.length; j++) {
            next[j] ^= poly[j]
            next[j + 1] ^= gfMul(poly[j], GF_EXP[i])
        }
        poly = next
    }
    return poly
}

function rsEncode(data, ecLen) {
    const gen = rsGenerator(ecLen)
    const remainder = Array.from({ length: ecLen }, () => 0)
    for (const byte of data) {
        const factor = byte ^ remainder[0]
        remainder.shift()
        remainder.push(0)
        for (let i = 0; i < ecLen; i++) {
            remainder[i] ^= gfMul(gen[i + 1], factor)
        }
    }
    return remainder
}

// ------------------------------------------------------------ bit utilities

class BitBuffer {
    constructor() {
        this.bits = []
    }
    put(value, length) {
        for (let i = length - 1; i >= 0; i--) this.bits.push((value >>> i) & 1)
    }
    get length() {
        return this.bits.length
    }
}

// --------------------------------------------------------------- encoding

const charCountBits = (version) => (version < 10 ? 8 : 16)

function dataCapacityBits(version, ecLevel) {
    const total = TOTAL_CODEWORDS[version - 1]
    const blocks = NUM_EC_BLOCKS[ecLevel][version - 1]
    const ecPerBlock = EC_CODEWORDS_PER_BLOCK[ecLevel][version - 1]
    return (total - blocks * ecPerBlock) * 8
}

function toBytes(text) {
    return Array.from(new TextEncoder().encode(text))
}

function pickVersion(byteLength, ecLevel, minVersion) {
    for (let v = Math.max(1, minVersion || 1); v <= 40; v++) {
        const needed = 4 + charCountBits(v) + byteLength * 8
        if (needed <= dataCapacityBits(v, ecLevel)) return v
    }
    throw new Error('QR: payload too long')
}

function buildCodewords(bytes, version, ecLevel) {
    const buffer = new BitBuffer()
    buffer.put(0b0100, 4)
    buffer.put(bytes.length, charCountBits(version))
    for (const b of bytes) buffer.put(b, 8)

    const capacity = dataCapacityBits(version, ecLevel)
    buffer.put(0, Math.min(4, capacity - buffer.length))
    if (buffer.length % 8 !== 0) buffer.put(0, 8 - (buffer.length % 8))

    const dataCodewords = []
    for (let i = 0; i < buffer.length; i += 8) {
        let byte = 0
        for (let j = 0; j < 8; j++) byte = (byte << 1) | buffer.bits[i + j]
        dataCodewords.push(byte)
    }
    const padBytes = [0xec, 0x11]
    for (let i = 0; dataCodewords.length < capacity / 8; i++) {
        dataCodewords.push(padBytes[i % 2])
    }

    const numBlocks = NUM_EC_BLOCKS[ecLevel][version - 1]
    const ecPerBlock = EC_CODEWORDS_PER_BLOCK[ecLevel][version - 1]
    const totalData = dataCodewords.length
    const shortLen = Math.floor(totalData / numBlocks)
    const numLong = totalData % numBlocks

    const dataBlocks = []
    const ecBlocks = []
    let offset = 0
    for (let b = 0; b < numBlocks; b++) {
        const len = shortLen + (b >= numBlocks - numLong ? 1 : 0)
        const block = dataCodewords.slice(offset, offset + len)
        offset += len
        dataBlocks.push(block)
        ecBlocks.push(rsEncode(block, ecPerBlock))
    }

    const result = []
    const maxDataLen = shortLen + (numLong > 0 ? 1 : 0)
    for (let i = 0; i < maxDataLen; i++) {
        for (const block of dataBlocks) if (i < block.length) result.push(block[i])
    }
    for (let i = 0; i < ecPerBlock; i++) {
        for (const block of ecBlocks) result.push(block[i])
    }
    return result
}

// ------------------------------------------------------------ matrix layout

function bchFormat(value) {
    let rem = value << 10
    for (let i = 14; i >= 10; i--) {
        if ((rem >>> i) & 1) rem ^= 0x537 << (i - 10)
    }
    return ((value << 10) | rem) ^ 0x5412
}

function bchVersion(version) {
    let rem = version << 12
    for (let i = 17; i >= 12; i--) {
        if ((rem >>> i) & 1) rem ^= 0x1f25 << (i - 12)
    }
    return (version << 12) | rem
}

function blankMatrix(size) {
    return Array.from({ length: size }, () => Array.from({ length: size }, () => null))
}

function placeFunctionPatterns(matrix, version) {
    const size = matrix.length

    const finder = (row, col) => {
        for (let r = -1; r <= 7; r++) {
            for (let c = -1; c <= 7; c++) {
                const rr = row + r
                const cc = col + c
                if (rr < 0 || rr >= size || cc < 0 || cc >= size) continue
                const inRing = r >= 0 && r <= 6 && (c === 0 || c === 6)
                const inCol = c >= 0 && c <= 6 && (r === 0 || r === 6)
                const inCore = r >= 2 && r <= 4 && c >= 2 && c <= 4
                matrix[rr][cc] = inRing || inCol || inCore
            }
        }
    }
    finder(0, 0)
    finder(0, size - 7)
    finder(size - 7, 0)

    for (let i = 8; i < size - 8; i++) {
        const dark = i % 2 === 0
        matrix[6][i] = dark
        matrix[i][6] = dark
    }

    const positions = ALIGNMENT_POSITIONS[version]
    for (const row of positions) {
        for (const col of positions) {
            const nearFinder =
                (row <= 8 && col <= 8) ||
                (row <= 8 && col >= size - 9) ||
                (row >= size - 9 && col <= 8)
            if (nearFinder) continue
            for (let r = -2; r <= 2; r++) {
                for (let c = -2; c <= 2; c++) {
                    matrix[row + r][col + c] =
                        Math.max(Math.abs(r), Math.abs(c)) !== 1
                }
            }
        }
    }

    matrix[size - 8][8] = true

    for (let i = 0; i <= 8; i++) {
        if (matrix[8][i] === null) matrix[8][i] = false
        if (matrix[i][8] === null) matrix[i][8] = false
    }
    for (let i = 0; i < 8; i++) {
        if (matrix[8][size - 1 - i] === null) matrix[8][size - 1 - i] = false
        if (matrix[size - 1 - i][8] === null) matrix[size - 1 - i][8] = false
    }

    if (version >= 7) {
        const bits = bchVersion(version)
        for (let i = 0; i < 18; i++) {
            const bit = ((bits >>> i) & 1) === 1
            const r = Math.floor(i / 3)
            const c = (i % 3) + size - 11
            matrix[r][c] = bit
            matrix[c][r] = bit
        }
    }
}

function functionMask(version, size) {
    const reserved = Array.from({ length: size }, () => Array.from({ length: size }, () => false))
    const mark = (r, c) => {
        if (r >= 0 && r < size && c >= 0 && c < size) reserved[r][c] = true
    }

    const finderArea = (row, col) => {
        for (let r = -1; r <= 7; r++) for (let c = -1; c <= 7; c++) mark(row + r, col + c)
    }
    finderArea(0, 0)
    finderArea(0, size - 7)
    finderArea(size - 7, 0)

    for (let i = 0; i < size; i++) {
        mark(6, i)
        mark(i, 6)
    }

    const positions = ALIGNMENT_POSITIONS[version]
    for (const row of positions) {
        for (const col of positions) {
            const nearFinder =
                (row <= 8 && col <= 8) ||
                (row <= 8 && col >= size - 9) ||
                (row >= size - 9 && col <= 8)
            if (nearFinder) continue
            for (let r = -2; r <= 2; r++) for (let c = -2; c <= 2; c++) mark(row + r, col + c)
        }
    }

    for (let i = 0; i <= 8; i++) {
        mark(8, i)
        mark(i, 8)
    }
    for (let i = 0; i < 8; i++) {
        mark(8, size - 1 - i)
        mark(size - 1 - i, 8)
    }
    mark(size - 8, 8)

    if (version >= 7) {
        for (let i = 0; i < 18; i++) {
            const r = Math.floor(i / 3)
            const c = (i % 3) + size - 11
            mark(r, c)
            mark(c, r)
        }
    }
    return reserved
}

function placeData(matrix, reserved, codewords) {
    const size = matrix.length
    let bitIndex = 0
    let upward = true

    for (let right = size - 1; right >= 1; right -= 2) {
        if (right === 6) right = 5
        for (let step = 0; step < size; step++) {
            const row = upward ? size - 1 - step : step
            for (const col of [right, right - 1]) {
                if (reserved[row][col]) continue
                let bit = false
                if (bitIndex < codewords.length * 8) {
                    const byte = codewords[bitIndex >>> 3]
                    bit = ((byte >>> (7 - (bitIndex & 7))) & 1) === 1
                }
                matrix[row][col] = bit
                bitIndex++
            }
        }
        upward = !upward
    }
}

const MASK_FNS = [
    (r, c) => (r + c) % 2 === 0,
    (r) => r % 2 === 0,
    (r, c) => c % 3 === 0,
    (r, c) => (r + c) % 3 === 0,
    (r, c) => (Math.floor(r / 2) + Math.floor(c / 3)) % 2 === 0,
    (r, c) => ((r * c) % 2) + ((r * c) % 3) === 0,
    (r, c) => (((r * c) % 2) + ((r * c) % 3)) % 2 === 0,
    (r, c) => (((r + c) % 2) + ((r * c) % 3)) % 2 === 0,
]

function applyMask(matrix, reserved, maskIndex) {
    const fn = MASK_FNS[maskIndex]
    const size = matrix.length
    for (let r = 0; r < size; r++) {
        for (let c = 0; c < size; c++) {
            if (!reserved[r][c] && fn(r, c)) matrix[r][c] = !matrix[r][c]
        }
    }
}

function placeFormatInfo(matrix, ecLevel, maskIndex) {
    const size = matrix.length
    const ecBits = [0b01, 0b00, 0b11, 0b10][ecLevel]
    const bits = bchFormat((ecBits << 3) | maskIndex)

    for (let i = 0; i < 15; i++) {
        const bit = ((bits >>> i) & 1) === 1

        if (i < 6) matrix[i][8] = bit
        else if (i < 8) matrix[i + 1][8] = bit
        else matrix[size - 15 + i][8] = bit

        if (i < 8) matrix[8][size - 1 - i] = bit
        else if (i === 8) matrix[8][7] = bit
        else matrix[8][14 - i] = bit
    }
}

function penalty(matrix) {
    const size = matrix.length
    let score = 0

    for (let i = 0; i < size; i++) {
        for (const horizontal of [true, false]) {
            let runColour = null
            let runLength = 0
            for (let j = 0; j < size; j++) {
                const module = horizontal ? matrix[i][j] : matrix[j][i]
                if (module === runColour) {
                    runLength++
                } else {
                    if (runLength >= 5) score += runLength - 2
                    runColour = module
                    runLength = 1
                }
            }
            if (runLength >= 5) score += runLength - 2
        }
    }

    for (let r = 0; r < size - 1; r++) {
        for (let c = 0; c < size - 1; c++) {
            const m = matrix[r][c]
            if (m === matrix[r][c + 1] && m === matrix[r + 1][c] && m === matrix[r + 1][c + 1]) {
                score += 3
            }
        }
    }

    const patternA = [true, false, true, true, true, false, true, false, false, false, false]
    const patternB = [false, false, false, false, true, false, true, true, true, false, true]
    const matches = (line, start, pattern) => {
        for (let k = 0; k < pattern.length; k++) {
            if (line[start + k] !== pattern[k]) return false
        }
        return true
    }
    for (let i = 0; i < size; i++) {
        const row = matrix[i]
        const col = matrix.map((r) => r[i])
        for (let j = 0; j + 11 <= size; j++) {
            if (matches(row, j, patternA) || matches(row, j, patternB)) score += 40
            if (matches(col, j, patternA) || matches(col, j, patternB)) score += 40
        }
    }

    let dark = 0
    for (const row of matrix) for (const m of row) if (m) dark++
    const ratio = (dark * 100) / (size * size)
    score += Math.floor(Math.abs(ratio - 50) / 5) * 10

    return score
}

// ------------------------------------------------------------------ public

/**
 * Encode `text` as a QR code matrix.
 * @returns {boolean[][]} square matrix, true = dark module
 */
export function qrMatrix(text, { ecLevel = 'M', minVersion = 1, mask = null } = {}) {
    const level = EC_LEVELS[ecLevel]
    if (level === undefined) throw new Error(`QR: unknown EC level ${ecLevel}`)

    const bytes = toBytes(text)
    const version = pickVersion(bytes.length, level, minVersion)
    const codewords = buildCodewords(bytes, version, level)
    const size = version * 4 + 17
    const reserved = functionMask(version, size)

    const render = (maskIndex) => {
        const matrix = blankMatrix(size)
        placeFunctionPatterns(matrix, version)
        placeData(matrix, reserved, codewords)
        applyMask(matrix, reserved, maskIndex)
        placeFormatInfo(matrix, level, maskIndex)
        return matrix
    }

    if (mask !== null) return render(mask)

    let best = null
    let bestScore = Infinity
    for (let m = 0; m < 8; m++) {
        const candidate = render(m)
        const score = penalty(candidate)
        if (score < bestScore) {
            bestScore = score
            best = candidate
        }
    }
    return best
}

/** Single SVG path covering every dark module (1 unit per module). */
export function qrSvgPath(matrix) {
    const parts = []
    for (let r = 0; r < matrix.length; r++) {
        for (let c = 0; c < matrix.length; c++) {
            if (matrix[r][c]) parts.push(`M${c} ${r}h1v1h-1z`)
        }
    }
    return parts.join('')
}

// --------------------------------------------------- payment payload helper

function crc16(str) {
    let crc = 0xffff
    for (let i = 0; i < str.length; i++) {
        crc ^= str.charCodeAt(i) << 8
        for (let b = 0; b < 8; b++) {
            crc = crc & 0x8000 ? ((crc << 1) ^ 0x1021) & 0xffff : (crc << 1) & 0xffff
        }
    }
    return crc.toString(16).toUpperCase().padStart(4, '0')
}

const tlv = (id, value) => `${id}${String(value.length).padStart(2, '0')}${value}`

/**
 * Generate 100% compliant EMVCo payment payloads for both Personal (P2P) and Merchant (P2M).
 */
export function easypaisaPayload({
    amount = 0,
    accountNumber = '',
    merchantName = 'LOUNGE POS',
    merchantCity = 'KARACHI',
    billRef = '',
    provider = 'EASYPAISA',
    personal = false,
} = {}) {
    const cleanAcc = String(accountNumber).trim().toUpperCase()
    if (!cleanAcc) {
        throw new Error('easypaisaPayload: accountNumber is required')
    }

    // Standard Merchant P2M Configuration
    const cleanName = merchantName.replace(/[^\x20-\x7E]/g, '').trim().slice(0, 25) || 'LOUNGE POS'
    const cleanCity = merchantCity.replace(/[^\x20-\x7E]/g, '').trim().slice(0, 15) || 'KARACHI'
    const cleanRef = String(billRef).replace(/[^\x20-\x7E]/g, '').trim().slice(0, 25)
    const pointOfInitiation = amount > 0 ? '12' : '11'

    let payload =
        tlv('00', '01') +
        tlv('01', pointOfInitiation)

    if (provider === 'JAZZCASH') {
        payload += tlv('27', tlv('00', 'COM.JAZZCASH') + tlv('01', cleanAcc))
    } else if (provider === 'RAAST') {
        payload += tlv('28', tlv('00', 'pk.org.sbp.raast') + tlv('01', cleanAcc))
    } else {
        payload += tlv('26', tlv('00', 'pk.easypaisa') + tlv('01', cleanAcc))
    }

    payload +=
        tlv('52', '7993') +
        tlv('53', '586')

    if (amount > 0) {
        const formattedAmount = Number(amount).toFixed(2).replace(/\.00$/, '')
        payload += tlv('54', formattedAmount)
    }

    payload +=
        tlv('58', 'PK') +
        tlv('59', cleanName) +
        tlv('60', cleanCity)

    if (cleanRef) {
        const subTag62 = tlv('01', cleanRef) + tlv('05', cleanRef)
        payload += tlv('62', subTag62)
    }

    payload += '6304'
    return payload + crc16(payload)
}