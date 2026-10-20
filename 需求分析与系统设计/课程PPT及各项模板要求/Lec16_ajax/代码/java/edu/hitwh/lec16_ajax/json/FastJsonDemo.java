package edu.hitwh.lec16_ajax.json;

import com.alibaba.fastjson.JSON;
import static com.alibaba.fastjson2.JSONObject.parseObject;

public class FastJsonDemo {
    public static void main(String[] args) {
        //1. 将Java对象转为JSON字符串
        User user = new User();
        user.setId(1);
        user.setUsername("zhangsan");
        user.setPassword("123");
        String jsonString = JSON.toJSONString(user);
        System.out.println(jsonString);//{"id":1,"password":"123","username":"zhangsan"}
        //2. 将JSON字符串转为Java对象
        //User u = parseObject(jsonString, User.class);
        User u = parseObject(jsonString, User.class);
        System.out.println(u);
    }
}
