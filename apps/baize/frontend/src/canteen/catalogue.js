// SAMPLE CANTEEN CATALOGUE — frontend only.
//
// Replace with GET /api/canteen/products when the backend lands. The shape here
// is what the UI expects, so a fetch can drop straight in:
//   { id, name, category, price, stock, emoji, tags? }
//
// `stock` drives the low/out-of-stock states; send null for unlimited items
// (a made-to-order tea has no shelf count).

export const CATEGORIES = [
    { id: 'all', label: 'All', imgUrl: '/all.png' },
    { id: 'hot', label: 'Hot Drinks', imgUrl: '/hot-drink.png' },
    { id: 'cold', label: 'Cold Drinks', imgUrl: '/softdrink.png' },
    { id: 'snacks', label: 'Snacks', imgUrl: '/snack.png' },
    { id: 'meals', label: 'Meals', imgUrl: '/fried-rice.png' },
    { id: 'sweets', label: 'Sweets', imgUrl: '/cupcake.png' },
    { id: 'smokes', label: 'Smokes', imgUrl: '/cigarrete.png' },
]

export const PRODUCTS = [
    { id: 1, name: 'Doodh Patti', category: 'hot', price: 120, stock: null, emoji: '☕' },
    { id: 2, name: 'Green Tea', category: 'hot', price: 90, stock: null, emoji: '🍵' },
    { id: 3, name: 'Coffee', category: 'hot', price: 180, stock: null, emoji: '☕' },
    { id: 4, name: 'Kashmiri Chai', category: 'hot', price: 200, stock: null, emoji: '🫖' },

    { id: 10, name: 'Coke 345ml', category: 'cold', price: 110, stock: 24, emoji: '🥤' },
    { id: 11, name: 'Sprite 345ml', category: 'cold', price: 110, stock: 6, emoji: '🥤' },
    { id: 12, name: 'Sting', category: 'cold', price: 100, stock: 3, emoji: '⚡' },
    { id: 13, name: 'Mineral Water', category: 'cold', price: 70, stock: 48, emoji: '💧' },
    { id: 14, name: 'Fresh Lime', category: 'cold', price: 150, stock: null, emoji: '🍋' },
    { id: 15, name: 'Red Bull', category: 'cold', price: 350, stock: 0, emoji: '🐂' },

    { id: 20, name: 'Lays Masala', category: 'snacks', price: 80, stock: 18, emoji: '🥔' },
    { id: 21, name: 'Kurkure', category: 'snacks', price: 60, stock: 22, emoji: '🌽' },
    { id: 22, name: 'Peanuts', category: 'snacks', price: 100, stock: 9, emoji: '🥜' },
    { id: 23, name: 'Samosa', category: 'snacks', price: 50, stock: 12, emoji: '🥟' },
    { id: 24, name: 'French Fries', category: 'snacks', price: 250, stock: null, emoji: '🍟' },

    { id: 30, name: 'Chicken Roll', category: 'meals', price: 320, stock: null, emoji: '🌯' },
    { id: 31, name: 'Zinger Burger', category: 'meals', price: 450, stock: null, emoji: '🍔' },
    { id: 32, name: 'Club Sandwich', category: 'meals', price: 380, stock: null, emoji: '🥪' },
    { id: 33, name: 'Chicken Karahi', category: 'meals', price: 900, stock: null, emoji: '🍲' },

    { id: 40, name: 'Dairy Milk', category: 'sweets', price: 150, stock: 14, emoji: '🍫' },
    { id: 41, name: 'Snickers', category: 'sweets', price: 180, stock: 4, emoji: '🍫' },
    { id: 42, name: 'Ice Cream Cone', category: 'sweets', price: 130, stock: 7, emoji: '🍦' },

    { id: 50, name: 'Marlboro', category: 'smokes', price: 480, stock: 11, emoji: '🚬' },
    { id: 51, name: 'Gold Leaf', category: 'smokes', price: 420, stock: 2, emoji: '🚬' },
    { id: 52, name: 'Lighter', category: 'smokes', price: 60, stock: 30, emoji: '🔥' },
]

/** Sample till history so the Recent panel isn't empty on first load. */
export const RECENT_ORDERS = [
    { id: 'C-1043', target: 'Snooker #2', items: 3, total: 470, at: '8:42 PM', method: 'cash' },
    { id: 'C-1042', target: 'Walk-in', items: 1, total: 110, at: '8:31 PM', method: 'easypaisa' },
    { id: 'C-1041', target: 'Pool #1', items: 5, total: 1240, at: '8:12 PM', method: 'cash' },
    { id: 'C-1040', target: 'PlayStation #3', items: 2, total: 560, at: '7:58 PM', method: 'jazzcash' },
]

export const PAYMENT_METHODS = [
    { id: 'cash', label: 'Cash', emoji: '💵' },
    { id: 'easypaisa', label: 'EasyPaisa', emoji: '📱' },
    { id: 'jazzcash', label: 'JazzCash', emoji: '📲' },
    { id: 'tab', label: 'Add to Tab', emoji: '🧾' },
]

export const LOW_STOCK_THRESHOLD = 5