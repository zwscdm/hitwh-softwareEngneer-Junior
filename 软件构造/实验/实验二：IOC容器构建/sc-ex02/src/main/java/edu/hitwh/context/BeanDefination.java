package edu.hitwh.context;

/**
 * 需要被IoC容器管理的bean的基本信息
 */
public class BeanDefination {
    private String beanName; // Bean的名字
    private Class beanClass; // Bean的Class对象
    private String scope;    // Bean的作用域（实验二新增）

    public BeanDefination(String beanName, Class beanClass, String scope) {
        this.beanName = beanName;
        this.beanClass = beanClass;
        this.scope = scope;
    }

    public String getBeanName() {
        return beanName;
    }
    public Class getBeanClass() {
        return beanClass;
    }

    public String getScope() {
        return scope;
    }

    @Override
    public String toString() {
        return "BeanDefination{" +
                "beanName='" + beanName + '\'' +
                ", beanClass=" + beanClass +
                ", scope='" + scope + '\'' +
                '}';
    }
}
