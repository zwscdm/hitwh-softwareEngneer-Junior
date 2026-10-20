package edu.hitwh.repository.impl;

import edu.hitwh.context.Component;
import edu.hitwh.repository.OrderRepo;

import java.util.Arrays;
import java.util.List;
@Component
public class OrderRepoImpl implements OrderRepo {
    @Override
    public List<String> findAll() {
        return Arrays.asList("1", "2", "3", "4", "5");
    }
}
