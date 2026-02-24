import CryptoJS from "crypto-js";

/**
 * MD5 加密
 * @param text 待加密文本
 * @returns 加密后的字符串
 */
export const encryptMD5 = (text: string): string => {
	return CryptoJS.MD5(text).toString(CryptoJS.enc.Hex);
};

/**
 * 密码加密（使用 MD5）
 * @param password 明文密码
 * @returns 加密后的密码
 */
export const encryptPassword = (password: string): string => {
	return encryptMD5(password);
};
