const axios = require('axios');

/**
 * 🛰 5SIM_API_SERVICE // IMPERIAL_SMS_NODE
 * Version: 1.0.0
 * Documentation: https://5sim.net/docs/v1
 */

class FiveSimAPI {
    constructor(apiKey) {
        this.apiKey = apiKey;
        this.baseUrl = 'https://5sim.net/v1/user';
        this.client = axios.create({
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'Accept': 'application/json'
            }
        });
    }

    // 1. Проверка профиля и баланса
    async getProfile() {
        try {
            const response = await this.client.get(`${this.baseUrl}/profile`);
            return response.data;
        } catch (error) {
            console.error('[5SIM] Profile Error:', error.response?.data || error.message);
            throw error;
        }
    }

    // 2. Получение цен и наличия
    async getProducts(country = 'russia', operator = 'any') {
        try {
            const response = await this.client.get(`https://5sim.net/v1/guest/products/${country}/${operator}`);
            return response.data;
        } catch (error) {
            console.error('[5SIM] Products Error:', error.response?.data || error.message);
            throw error;
        }
    }

    // 3. Покупка номера (Активация)
    async buyNumber(country = 'russia', operator = 'any', product = 'telegram') {
        try {
            const response = await this.client.get(`${this.baseUrl}/buy/activation/${country}/${operator}/${product}`);
            return response.data;
        } catch (error) {
            console.error('[5SIM] Purchase Error:', error.response?.data || error.message);
            throw error;
        }
    }

    // 4. Проверка статуса заказа (получение SMS)
    async checkOrder(orderId) {
        try {
            const response = await this.client.get(`${this.baseUrl}/check/${orderId}`);
            return response.data;
        } catch (error) {
            console.error('[5SIM] Check Order Error:', error.response?.data || error.message);
            throw error;
        }
    }

    // 5. Завершение заказа (после получения SMS)
    async finishOrder(orderId) {
        try {
            const response = await this.client.get(`${this.baseUrl}/finish/${orderId}`);
            return response.data;
        } catch (error) {
            console.error('[5SIM] Finish Error:', error.response?.data || error.message);
            throw error;
        }
    }

    // 6. Отмена заказа (если SMS не пришло)
    async cancelOrder(orderId) {
        try {
            const response = await this.client.get(`${this.baseUrl}/cancel/${orderId}`);
            return response.data;
        } catch (error) {
            console.error('[5SIM] Cancel Error:', error.response?.data || error.message);
            throw error;
        }
    }
}

module.exports = FiveSimAPI;
