package cn.techkg.common.constant;

import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public enum BusinessErrorCode {

    SUCCESS(200, "操作成功"),
    FAILURE(500, "操作失败"),
    UNAUTHORIZED(401, "未授权"),
    FORBIDDEN(403, "无权限"),
    NOT_FOUND(404, "资源不存在"),
    PARAM_ERROR(400, "参数错误");

    private final int code;
    private final String message;
}
