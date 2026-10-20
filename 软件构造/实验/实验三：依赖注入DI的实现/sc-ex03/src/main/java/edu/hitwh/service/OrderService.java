package edu.hitwh.service;

import java.util.List;

/**
 * 订单业务接口，与订单相关的业务均在此接口中定义
 * 为了方便测试，List<> 中的泛型定义成String，实际上应该是List<Order>
 */
public interface OrderService {
    List<String> findAll();
}
