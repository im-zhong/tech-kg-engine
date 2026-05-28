package cn.techkg.auth.granter;

public interface ITokenGranter {

    String GRANT_TYPE = "password";

    Object grant();
}
